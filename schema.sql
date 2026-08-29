-- =========================================================
-- LIBRARY MANAGEMENT SYSTEM - DATABASE SCHEMA
-- =========================================================
-- Import this file in phpMyAdmin (or run via MySQL CLI)
-- to create the database and all required tables.
-- =========================================================

CREATE DATABASE IF NOT EXISTS library_system;
USE library_system;

-- ---------------------------------------------------------
-- ADMIN USERS
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin'
);

-- Default admin login:
--   username: admin
--   password: admin123
INSERT INTO users (username, password, role)
VALUES (
    'admin',
    'scrypt:32768:8:1$cv46UldnXLlp6M44$57954bd4ab11df1bb52ff25512cde595fa605aea3e16489dc4920721b5d254cb7b83594f1761b1a83fde12441bc690f980de340207ee8622d5906acc3e4e6ce6',
    'admin'
);

-- ---------------------------------------------------------
-- MEMBERS (library members / students who borrow books)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20)
);

INSERT INTO members (member_code, name, email, phone) VALUES
('M001', 'Ravi Kumar', 'ravi@example.com', '9876543210'),
('M002', 'Priya Sharma', 'priya@example.com', '9876500000');

-- ---------------------------------------------------------
-- BOOKS
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    author VARCHAR(100),
    category VARCHAR(50),
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1
);

INSERT INTO books (title, author, category, total_copies, available_copies) VALUES
('The Alchemist', 'Paulo Coelho', 'Fiction', 3, 3),
('Clean Code', 'Robert C. Martin', 'Programming', 2, 2),
('Wings of Fire', 'A.P.J. Abdul Kalam', 'Biography', 4, 4);

-- ---------------------------------------------------------
-- ISSUED BOOKS (borrow / return records)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS issued_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE DEFAULT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Issued',
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);
