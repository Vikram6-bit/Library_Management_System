import mysql.connector


def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="library_system"
    )

    return connection


if __name__ == "__main__":
    connection = get_connection()
    print("Database connected successfully!")
    connection.close()
