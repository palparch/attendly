import sqlite3
from flask import current_app, g

def get_db():
	if "db" not in g:
		g.db = sqlite3.connect(current_app.config["DATABASE"])
		g.db.row_factory = sqlite3.Row
		g.db.execute("PRAGMA foreign_keys = ON")
	return g.db

def close_db(error=None):
	db = g.pop("db", None)
	if db is not None:
		db.close()

def init_db():
	db = get_db()
	db.executescript("""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT NOT NULL UNIQUE,
			password_hash TEXT NOT NULL,
			role TEXT NOT NULL CHECK(role IN ('teacher', 'student')),
			created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS students (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL UNIQUE,
			full_name TEXT NOT NULL,
			roll_number TEXT NOT NULL UNIQUE,
			class_name TEXT NOT NULL,
			FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
		);

		CREATE TABLE IF NOT EXISTS attendance (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			student_id INTEGER NOT NULL,
			attendance_date TEXT NOT NULL,
			subject TEXT NOT NULL,
			status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
			marked_by INTEGER NOT NULL,
			created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
			FOREIGN KEY(marked_by) REFERENCES users(id),
			UNIQUE(student_id, attendance_date, subject)
		);

		CREATE TABLE IF NOT EXISTS student_photos (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			student_id INTEGER NOT NULL,
			photo_path TEXT NOT NULL,
			FOREIGN KEY(student_id)
			REFERENCES students(id) ON DELETE CASCADE
		);


	""")
	db.commit()

def init_app(app):
	app.teardown_appcontext(close_db)
