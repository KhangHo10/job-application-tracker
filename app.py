"""Job Application Tracker - Flask application (routes, validation, rendering).

All SQL lives in database.py; this module only handles HTTP concerns.
"""
import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-insecure-key")


@app.route("/")
def dashboard():
    return "Job Application Tracker is running."


if __name__ == "__main__":
    app.run(debug=True)
