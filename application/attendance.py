from datetime import date, timedelta
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from .auth import login_required, teacher_required
from .database import get_db

attendance = Blueprint("attendance", __name__)

def attendance_summary(db, student_id, subject=None):
    params = [student_id]
    query = """SELECT status, attendance_date, subject
               FROM attendance WHERE student_id = ?"""
    if subject:
        query += " AND subject = ?"
        params.append(subject)
    rows = db.execute(query, params).fetchall()
    total = len(rows)
    present = sum(1 for row in rows if row["status"] == "Present")
    percentage = round((present / total) * 100, 1) if total else 0.0
    recent = sorted(rows, key=lambda row: row["attendance_date"], reverse=True)[:10]
    recent_absences = sum(1 for row in recent if row["status"] == "Absent")
    return {
        "total": total,
        "present": present,
        "absent": total - present,
        "percentage": percentage,
        "recent_absences": recent_absences,
    }

@attendance.route("/teacher")
@teacher_required
def teacher_dashboard():
    db = get_db()
    selected_date = request.args.get("date", date.today().isoformat())
    subject = request.args.get("subject", "General").strip() or "General"

    student_rows = db.execute(
        "SELECT * FROM students ORDER BY class_name, roll_number"
    ).fetchall()

    student_data = []
    for student in student_rows:
        summary = attendance_summary(db, student["id"], subject)
        recent = summary["recent_absences"]
        student_data.append({
            "student": student,
            "summary": summary,
            "flag": summary["percentage"] < 75 and summary["total"] > 0,
            "repeated": recent >= 3,
        })

    today_records = db.execute(
        """SELECT student_id, status FROM attendance
           WHERE attendance_date = ? AND subject = ?""",
        (selected_date, subject),
    ).fetchall()
    marked = {row["student_id"]: row["status"] for row in today_records}

    return render_template(
        "teacher.html",
        students=student_data,
        selected_date=selected_date,
        subject=subject,
        marked=marked,
    )

@attendance.route("/attendance/mark/<int:student_id>", methods=["POST"])
@teacher_required
def mark_attendance(student_id):
    attendance_date = request.form.get("attendance_date", date.today().isoformat())
    subject = request.form.get("subject", "General").strip() or "General"
    status = request.form.get("status")
    if status not in ("Present", "Absent"):
        flash("Invalid attendance status.", "danger")
        return redirect(url_for("attendance.teacher_dashboard"))

    db = get_db()
    student = db.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("attendance.teacher_dashboard"))

    db.execute(
        """INSERT INTO attendance
           (student_id, attendance_date, subject, status, marked_by)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(student_id, attendance_date, subject)
           DO UPDATE SET status = excluded.status, marked_by = excluded.marked_by""",
        (student_id, attendance_date, subject, status, session["user_id"]),
    )
    db.commit()
    flash("Attendance saved.", "success")
    return redirect(url_for(
        "attendance.teacher_dashboard",
        date=attendance_date,
        subject=subject,
    ))

@attendance.route("/student")
@login_required
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("attendance.teacher_dashboard"))

    db = get_db()
    student = db.execute(
        "SELECT * FROM students WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    if not student:
        flash("Student profile not found. Please contact the teacher.", "danger")
        return redirect(url_for("auth.logout"))

    records = db.execute(
        """SELECT attendance_date, subject, status FROM attendance
           WHERE student_id = ?
           ORDER BY attendance_date DESC, subject""",
        (student["id"],),
    ).fetchall()

    summary = attendance_summary(db, student["id"])
    subjects = db.execute(
        "SELECT DISTINCT subject FROM attendance WHERE student_id = ? ORDER BY subject",
        (student["id"],),
    ).fetchall()
    subject_summaries = [
        (item["subject"], attendance_summary(db, student["id"], item["subject"]))
        for item in subjects
    ]

    return render_template(
        "student.html",
        student=student,
        records=records,
        summary=summary,
        subject_summaries=subject_summaries,
    )
