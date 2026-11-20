from getpass import getpass
from pathlib import Path
import sqlite3
from werkzeug.security import generate_password_hash

db_path = Path(__file__).parent / "instance" / "attendly.db"
db_path.parent.mkdir(exist_ok=True)

username = input("Teacher username: ").strip()
password = getpass("Teacher password (at least 8 characters): ")

if not username or len(password) < 8:
    raise SystemExit("Username is required and password must be at least 8 characters.")

connection = sqlite3.connect(db_path)
try:
    connection.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'teacher')",
        (username, generate_password_hash(password)),
    )
    connection.commit()
    print("Teacher account created.")
except sqlite3.IntegrityError:
    print("That username already exists.")
finally:
    connection.close()
