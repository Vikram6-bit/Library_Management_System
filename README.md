# Library Management System

A Flask + MySQL web app for managing a library — admin manages books, members,
and book issue/return records; members log in separately to view their own
borrowing history.

## Features

- Two login types: **Admin** (username + hashed password) and **Member**
  (member code + email, no password needed — read-only access)
- Admin dashboard with live stats (total books, members, currently issued,
  overdue count) and a Chart.js bar chart of books by category
- Full CRUD for Books and Members (add / edit / delete / search)
- Issue a book to a member (auto-decreases available copies, sets a due date)
- Return a book (auto-increases available copies, records return date)
- Issued/Returned records list with overdue highlighting
- CSV export of all issue records
- "Popular Books" leaderboard (SQL `JOIN` + `GROUP BY` + `ORDER BY` + `LIMIT`)
- Member dashboard showing their own borrow history

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL (`mysql-connector-python`)
- **Auth:** Flask sessions, Werkzeug password hashing
- **Frontend:** HTML, CSS, Jinja2 templates, Chart.js (CDN)

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create the database: open phpMyAdmin (or the MySQL CLI) and import
   `schema.sql`. This creates the `library_system` database, all tables,
   a default admin account, and a couple of sample books/members.

3. Run the app:
   ```
   python app.py
   ```
   It runs on **http://127.0.0.1:5001** (different port from the Student
   Result project, so both can run at the same time).

## Default Logins

**Admin**
- Username: `admin`
- Password: `admin123`

**Member** (sample data)
- Member Code: `M001`
- Email: `ravi@example.com`

## Project Structure

```
Library_Management_System/
├── app.py
├── database.py
├── schema.sql
├── requirements.txt
├── static/
│   └── style.css
└── templates/
    ├── home.html
    ├── admin_login.html
    ├── member_login.html
    ├── admin_dashboard.html
    ├── member_dashboard.html
    ├── books.html
    ├── add_book.html
    ├── edit_book.html
    ├── members.html
    ├── add_member.html
    ├── edit_member.html
    ├── issue_book.html
    ├── issued_books.html
    ├── popular_books.html
    └── error.html
```
