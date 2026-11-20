from flask import Flask

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "attendly-development-key"

    @app.route("/")
    def home():
        return "<h1>Welcome to Attendly!</h1>"

    return app
