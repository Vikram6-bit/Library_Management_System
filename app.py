from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response
)

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, timedelta
import csv
import io


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)
app.secret_key = "library_secret_key_123"


# =========================================================
# MYSQL CONNECTION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="library_system"
    )


# =========================================================
# ACCESS DECORATORS
# =========================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Please login as admin first.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def member_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "member":
            flash("Please login first.", "error")
            return redirect(url_for("member_login"))
        return f(*args, **kwargs)
    return decorated_function


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("home.html")


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                "SELECT id, username, password, role FROM users WHERE username = %s",
                (username,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = "admin"
                return redirect(url_for("admin_dashboard"))

            flash("Invalid username or password.", "error")

        except Error as e:
            flash("Database error: " + str(e), "error")

        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    return render_template("admin_login.html")


# =========================================================
# MEMBER LOGIN
# =========================================================

@app.route("/member-login", methods=["GET", "POST"])
def member_login():

    if request.method == "POST":

        member_code = request.form.get("member_code", "").strip()
        email = request.form.get("email", "").strip()

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                "SELECT id, name, member_code, email FROM members WHERE member_code = %s AND email = %s",
                (member_code, email)
            )

            member = cursor.fetchone()

            if member:
                session.clear()
                session["role"] = "member"
                session["member_id"] = member["id"]
                session["member_name"] = member["name"]
                session["member_code"] = member["member_code"]
                return redirect(url_for("member_dashboard"))

            flash("Invalid Member Code or Email.", "error")

        except Error as e:
            flash("Database error: " + str(e), "error")

        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    return render_template("member_login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM books")
    total_books = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM members")
    total_members = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM issued_books WHERE status = 'Issued'")
    total_issued = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM issued_books WHERE status = 'Issued' AND due_date < %s",
        (date.today(),)
    )
    total_overdue = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT category, COUNT(*) AS count
        FROM books
        GROUP BY category
        """
    )
    category_rows = cursor.fetchall()

    cursor.close()
    db.close()

    category_labels = [row["category"] for row in category_rows]
    category_counts = [row["count"] for row in category_rows]

    return render_template(
        "admin_dashboard.html",
        total_books=total_books,
        total_members=total_members,
        total_issued=total_issued,
        total_overdue=total_overdue,
        category_labels=category_labels,
        category_counts=category_counts
    )


# =========================================================
# MEMBER DASHBOARD
# =========================================================

@app.route("/member-dashboard")
@member_required
def member_dashboard():

    member_id = session.get("member_id")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            books.title,
            books.author,
            issued_books.issue_date,
            issued_books.due_date,
            issued_books.return_date,
            issued_books.status
        FROM issued_books
        INNER JOIN books ON issued_books.book_id = books.id
        WHERE issued_books.member_id = %s
        ORDER BY issued_books.issue_date DESC
        """,
        (member_id,)
    )

    records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "member_dashboard.html",
        records=records
    )


# =========================================================
# VIEW / SEARCH BOOKS
# =========================================================

@app.route("/books", methods=["GET"])
@admin_required
def books():

    search = request.args.get("search", "").strip()

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if search:
        value = "%" + search + "%"
        cursor.execute(
            """
            SELECT * FROM books
            WHERE title LIKE %s OR author LIKE %s OR category LIKE %s
            ORDER BY id
            """,
            (value, value, value)
        )
    else:
        cursor.execute("SELECT * FROM books ORDER BY id")

    book_rows = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("books.html", books=book_rows, search=search)


# =========================================================
# ADD BOOK
# =========================================================

@app.route("/add_book", methods=["GET", "POST"])
@admin_required
def add_book():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        total_copies = request.form.get("total_copies", "1").strip()

        if not title:
            flash("Title is required.", "error")
            return render_template("add_book.html")

        try:
            total_copies = int(total_copies)
            if total_copies < 1:
                raise ValueError
        except ValueError:
            flash("Total copies must be a positive number.", "error")
            return render_template("add_book.html")

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO books (title, author, category, total_copies, available_copies)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (title, author, category, total_copies, total_copies)
            )

            db.commit()

            flash("Book added successfully!", "success")
            return redirect(url_for("books"))

        except Error as e:
            if db:
                db.rollback()
            flash("Database error: " + str(e), "error")
            return render_template("add_book.html")

        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    return render_template("add_book.html")


# =========================================================
# EDIT BOOK
# =========================================================

@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
@admin_required
def edit_book(book_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        total_copies = request.form.get("total_copies", "1").strip()

        if not title:
            flash("Title is required.", "error")
            return redirect(url_for("edit_book", book_id=book_id))

        try:
            total_copies = int(total_copies)
        except ValueError:
            flash("Total copies must be a number.", "error")
            return redirect(url_for("edit_book", book_id=book_id))

        # Keep available_copies in sync: figure out how many are currently issued
        cursor.execute(
            "SELECT total_copies, available_copies FROM books WHERE id = %s",
            (book_id,)
        )
        current = cursor.fetchone()

        if not current:
            cursor.close()
            db.close()
            return render_template("error.html", message="Book not found.")

        issued_count = current["total_copies"] - current["available_copies"]
        new_available = max(total_copies - issued_count, 0)

        cursor.execute(
            """
            UPDATE books
            SET title = %s, author = %s, category = %s,
                total_copies = %s, available_copies = %s
            WHERE id = %s
            """,
            (title, author, category, total_copies, new_available, book_id)
        )

        db.commit()
        cursor.close()
        db.close()

        flash("Book updated successfully.", "success")
        return redirect(url_for("books"))

    cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cursor.fetchone()

    cursor.close()
    db.close()

    if not book:
        return render_template("error.html", message="Book not found.")

    return render_template("edit_book.html", book=book)


# =========================================================
# DELETE BOOK
# =========================================================

@app.route("/delete_book/<int:book_id>")
@admin_required
def delete_book(book_id):

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM issued_books WHERE book_id = %s", (book_id,))
    cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))

    db.commit()
    cursor.close()
    db.close()

    flash("Book deleted successfully.", "success")
    return redirect(url_for("books"))


# =========================================================
# VIEW / ADD / EDIT / DELETE MEMBERS
# =========================================================

@app.route("/members")
@admin_required
def members():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM members ORDER BY id")
    member_rows = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("members.html", members=member_rows)


@app.route("/add_member", methods=["GET", "POST"])
@admin_required
def add_member():

    if request.method == "POST":

        member_code = request.form.get("member_code", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not member_code or not name:
            flash("Member code and name are required.", "error")
            return render_template("add_member.html")

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute("SELECT id FROM members WHERE member_code = %s", (member_code,))
            if cursor.fetchone():
                flash("Member code already exists.", "error")
                return render_template("add_member.html")

            cursor.execute(
                "INSERT INTO members (member_code, name, email, phone) VALUES (%s, %s, %s, %s)",
                (member_code, name, email, phone)
            )

            db.commit()
            flash("Member added successfully!", "success")
            return redirect(url_for("members"))

        except Error as e:
            if db:
                db.rollback()
            flash("Database error: " + str(e), "error")
            return render_template("add_member.html")

        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    return render_template("add_member.html")


@app.route("/edit_member/<int:member_id>", methods=["GET", "POST"])
@admin_required
def edit_member(member_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name:
            flash("Name is required.", "error")
            return redirect(url_for("edit_member", member_id=member_id))

        cursor.execute(
            "UPDATE members SET name = %s, email = %s, phone = %s WHERE id = %s",
            (name, email, phone, member_id)
        )

        db.commit()
        cursor.close()
        db.close()

        flash("Member updated successfully.", "success")
        return redirect(url_for("members"))

    cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
    member = cursor.fetchone()

    cursor.close()
    db.close()

    if not member:
        return render_template("error.html", message="Member not found.")

    return render_template("edit_member.html", member=member)


@app.route("/delete_member/<int:member_id>")
@admin_required
def delete_member(member_id):

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM issued_books WHERE member_id = %s", (member_id,))
    cursor.execute("DELETE FROM members WHERE id = %s", (member_id,))

    db.commit()
    cursor.close()
    db.close()

    flash("Member deleted successfully.", "success")
    return redirect(url_for("members"))


# =========================================================
# ISSUE BOOK
# =========================================================

@app.route("/issue_book", methods=["GET", "POST"])
@admin_required
def issue_book():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        book_id = request.form.get("book_id", "").strip()
        member_id = request.form.get("member_id", "").strip()
        due_days = request.form.get("due_days", "14").strip()

        if not book_id or not member_id:
            flash("Please select both a book and a member.", "error")
            return redirect(url_for("issue_book"))

        try:
            due_days = int(due_days)
        except ValueError:
            due_days = 14

        cursor.execute("SELECT available_copies FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()

        if not book or book["available_copies"] < 1:
            flash("This book is not available right now.", "error")
            return redirect(url_for("issue_book"))

        issue_date = date.today()
        due_date = issue_date + timedelta(days=due_days)

        cursor.execute(
            """
            INSERT INTO issued_books (book_id, member_id, issue_date, due_date, status)
            VALUES (%s, %s, %s, %s, 'Issued')
            """,
            (book_id, member_id, issue_date, due_date)
        )

        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id = %s",
            (book_id,)
        )

        db.commit()
        cursor.close()
        db.close()

        flash("Book issued successfully.", "success")
        return redirect(url_for("issued_books"))

    cursor.execute("SELECT id, title, available_copies FROM books WHERE available_copies > 0 ORDER BY title")
    available_books = cursor.fetchall()

    cursor.execute("SELECT id, name, member_code FROM members ORDER BY name")
    all_members = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("issue_book.html", books=available_books, members=all_members)


# =========================================================
# RETURN BOOK
# =========================================================

@app.route("/return_book/<int:record_id>")
@admin_required
def return_book(record_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM issued_books WHERE id = %s", (record_id,))
    record = cursor.fetchone()

    if not record or record["status"] == "Returned":
        cursor.close()
        db.close()
        flash("Invalid or already returned record.", "error")
        return redirect(url_for("issued_books"))

    cursor.execute(
        "UPDATE issued_books SET status = 'Returned', return_date = %s WHERE id = %s",
        (date.today(), record_id)
    )

    cursor.execute(
        "UPDATE books SET available_copies = available_copies + 1 WHERE id = %s",
        (record["book_id"],)
    )

    db.commit()
    cursor.close()
    db.close()

    flash("Book marked as returned.", "success")
    return redirect(url_for("issued_books"))


# =========================================================
# VIEW ISSUED BOOKS
# =========================================================

@app.route("/issued_books")
@admin_required
def issued_books():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            issued_books.id,
            books.title,
            members.name AS member_name,
            issued_books.issue_date,
            issued_books.due_date,
            issued_books.return_date,
            issued_books.status
        FROM issued_books
        INNER JOIN books ON issued_books.book_id = books.id
        INNER JOIN members ON issued_books.member_id = members.id
        ORDER BY issued_books.id DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    db.close()

    today = date.today()

    return render_template("issued_books.html", records=records, today=today)


# =========================================================
# POPULAR BOOKS (most issued)
# =========================================================

@app.route("/popular_books")
@admin_required
def popular_books():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            books.title,
            books.author,
            COUNT(issued_books.id) AS times_issued
        FROM issued_books
        INNER JOIN books ON issued_books.book_id = books.id
        GROUP BY books.id
        ORDER BY times_issued DESC
        LIMIT 5
        """
    )

    top_books = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("popular_books.html", top_books=top_books)


# =========================================================
# DOWNLOAD ISSUED BOOKS AS CSV
# =========================================================

@app.route("/download_issued_books")
@admin_required
def download_issued_books():

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT
            books.title,
            members.name,
            issued_books.issue_date,
            issued_books.due_date,
            issued_books.return_date,
            issued_books.status
        FROM issued_books
        INNER JOIN books ON issued_books.book_id = books.id
        INNER JOIN members ON issued_books.member_id = members.id
        ORDER BY issued_books.id DESC
        """
    )

    rows = cursor.fetchall()
    cursor.close()
    db.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Book", "Member", "Issue Date", "Due Date", "Return Date", "Status"])
    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=issued_books.csv"}
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html", message="Internal server error."), 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
