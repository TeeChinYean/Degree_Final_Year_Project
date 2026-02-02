# Green Point - Dynamic PHP Site
This project was generated from your uploaded PDF (Degree_Final_Year_Project.pdf) and modernized into a simple dynamic PHP website.

## Features
- User registration and login (session-based)
- Dashboard with points balance
- Item types listing (from PDF)
- Demo photo upload endpoint that "analyzes" an image filename and awards points
- Contact form recording to database

## Setup
1. Place files in your PHP-enabled server (e.g., XAMPP, LAMP).
2. Create a MySQL database `greenpoint` and a user `gp_user` with password `gp_pass` (or edit `config.php`).
3. Import the SQL schema in `init_db.sql`.
4. Make sure `uploads/` is writable by PHP.
5. Visit the site root in your browser.

## Note
The analyze function is a placeholder. Replace with a real model or API for production use.
