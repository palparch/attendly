
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
from werkzeug.security import generate_password_hash
from .auth import teacher_required
from .database import get_db

from pathlib import Path
from uuid import uuid4
from io import BytesIO

from PIL import Image, UnidentifiedImageError

students = Blueprint("students", __name__)


def process_photos(files):
    photos = []

    for file in files:
        data = file.read()

        if len(data) > 5 * 1024 * 1024:
            raise ValueError("Each image must be under 5 MB.")

        try:
            image = Image.open(BytesIO(data))
            image.verify()

            image = Image.open(BytesIO(data))
            image = image.convert("RGB")

        except (UnidentifiedImageError, OSError):
            raise ValueError("One of the uploaded files is not a valid image.")

        photos.append(image)

    return photos


@students.route("/students/register", methods=["GET", "POST"])
@teacher_required
def register_student():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        roll_number = request.form.get("roll_number", "").strip()
        class_name = request.form.get("class_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not all([full_name, roll_number, class_name, username, password]):
            flash("Please complete every field.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Use a password with at least 8 characters.", "danger")
            return render_template("register.html")

        photo_files = [
            file for file in request.files.getlist("photos")
            if file and file.filename
        ]

        consent = request.form.get("photo_consent") == "yes"

        if len(photo_files) > 5:
            flash("You can upload a maximum of 5 photographs.", "danger")
            return render_template("register.html")

        if photo_files and not consent:
            flash("Permission is required for photo enrollment.", "danger")
            return render_template("register.html")

        if consent and len(photo_files) != 5:
            flash("Please select exactly 5 photographs.", "danger")
            return render_template("register.html")

        try:
            photos = process_photos(photo_files)
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("register.html")

        db = get_db()
        saved_paths = []

        try:
            # Create the student login account
            cursor = db.execute(
                """INSERT INTO users
                   (username, password_hash, role)
                   VALUES (?, ?, 'student')""",
                (username, generate_password_hash(password)),
            )

            user_id = cursor.lastrowid

            # Create the student record
            cursor = db.execute(
                """INSERT INTO students
                   (user_id, full_name, roll_number, class_name)
                   VALUES (?, ?, ?, ?)""",
                (user_id, full_name, roll_number, class_name),
            )

            student_id = cursor.lastrowid

            # Store the student's reference photographs
            upload_dir = (
                Path(current_app.instance_path)
                / "uploads"
                / "student_faces"
                / str(student_id)
            )

            upload_dir.mkdir(parents=True, exist_ok=True)

            for image in photos:

                filename = f"{uuid4().hex}.jpg"
                filepath = upload_dir / filename

                image.save(filepath, format="JPEG", quality=95)
                saved_paths.append(filepath)

                relative_path = str(
                    filepath.relative_to(current_app.instance_path)
                )

                db.execute(
                    """INSERT INTO student_photos
                       (student_id, photo_path)
                       VALUES (?, ?)""",
                    (student_id, relative_path)
                )

            db.commit()

            flash(f"Student {full_name} registered.", "success")
            return redirect(url_for("attendance.teacher_dashboard"))

        except Exception:
            db.rollback()

            # Remove files if registration fails
            for filepath in saved_paths:
                filepath.unlink(missing_ok=True)

            flash(
                "Could not register student. Check that username and roll number are unique.",
                "danger"
            )

    return render_template("register.html")

