"""Job Application Tracker - Flask application (routes, validation, rendering).

All SQL lives in database.py; this module only handles HTTP concerns.

Endpoint names follow "<section>_<action>" (e.g. companies_edit) so the
nav bar can highlight the section a page belongs to.
"""
import os

from dotenv import load_dotenv
from flask import Flask, render_template

import database as db

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-insecure-key")


@app.errorhandler(db.DatabaseError)
def handle_database_error(error):
    app.logger.exception("Database error")
    return render_template("error.html", error=error), 500


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# Placeholders until each section is built.
@app.route("/companies")
def companies():
    return render_template("base.html", title="Companies")


@app.route("/jobs")
def jobs():
    return render_template("base.html", title="Jobs")


@app.route("/applications")
def applications():
    return render_template("base.html", title="Applications")


@app.route("/contacts")
def contacts():
    return render_template("base.html", title="Contacts")


@app.route("/job-match")
def job_match():
    return render_template("base.html", title="Job Match")


if __name__ == "__main__":
    app.run(debug=True)
