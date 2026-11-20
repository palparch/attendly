import os
from pathlib import Path
from flask import Flask, redirect, url_for
from .database import init_app, init_db

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.update(
        SECRET_KEY=os.environ.get("ATTENDLY_SECRET_KEY", "dev-only-change-this-key"),
        DATABASE=os.path.join(app.instance_path, "attendly.db"),
    )

    init_app(app)

    from .auth import auth
    from .students import students
    from .attendance import attendance

    app.register_blueprint(auth)
    app.register_blueprint(students)
    app.register_blueprint(attendance)

    @app.route("/")
    def home():
        from flask import session
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("role") == "teacher":
            return redirect(url_for("attendance.teacher_dashboard"))
        return redirect(url_for("attendance.student_dashboard"))

    with app.app_context():
        init_db()

    return app
