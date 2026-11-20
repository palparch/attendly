from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from .database import get_db

auth = Blueprint("auth", __name__)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

def teacher_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "teacher":
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for("attendance.student_dashboard"))
        return view(*args, **kwargs)
    return wrapped

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Logged in successfully.", "success")
            if user["role"] == "teacher":
                return redirect(url_for("attendance.teacher_dashboard"))
            return redirect(url_for("attendance.student_dashboard"))

        flash("Incorrect username or password.", "danger")

    return render_template("login.html")

@auth.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
