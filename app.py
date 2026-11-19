"""Job Application Tracker - Flask application (routes, validation, rendering).

All SQL lives in database.py; this module only handles HTTP concerns.

Endpoint names follow "<section>_<action>" (e.g. companies_edit) so the
nav bar can highlight the section a page belongs to.
"""
import os

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

import database as db
from validators import validate_company

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-insecure-key")


@app.errorhandler(db.DatabaseError)
def handle_database_error(error):
    app.logger.exception("Database error")
    return render_template("error.html", error=error), 500


# ---------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------

@app.template_filter("salary_range")
def salary_range(job):
    """Format a job's salary range, e.g. "$80,000–$105,000"."""
    low, high = job.get("salary_min"), job.get("salary_max")
    if low is not None and high is not None:
        return f"${low:,.0f}–${high:,.0f}"
    if low is not None:
        return f"From ${low:,.0f}"
    if high is not None:
        return f"Up to ${high:,.0f}"
    return "—"


@app.template_filter("plural")
def plural(count, word):
    """'1 job', '3 jobs'."""
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def cascade_message(counts):
    """Human-readable list of what a delete will also remove, e.g. '2 jobs, 1 contact'."""
    parts = [
        plural(counts[key], word)
        for key, word in (("job_count", "job"), ("application_count", "application"),
                          ("contact_count", "contact"))
        if key in counts and counts[key]
    ]
    return ", ".join(parts)


app.jinja_env.globals["cascade_message"] = cascade_message


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ---------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------

@app.route("/companies")
def companies():
    search = (request.args.get("q") or "").strip()
    return render_template("companies.html", companies=db.get_companies(search or None),
                           search=search)


@app.route("/companies/new", methods=["GET", "POST"])
def companies_new():
    if request.method == "POST":
        data, errors = validate_company(request.form)
        if not errors:
            company_id = db.create_company(data)
            flash(f"Added {data['company_name']}.", "success")
            return redirect(url_for("companies_detail", company_id=company_id))
        for error in errors:
            flash(error, "error")
        return render_template("company_form.html", form=request.form, company=None), 400
    return render_template("company_form.html", form={}, company=None)


@app.route("/companies/<int:company_id>")
def companies_detail(company_id):
    company = db.get_company(company_id) or abort(404)
    return render_template(
        "company_detail.html",
        company=company,
        jobs=db.get_company_jobs(company_id),
        contacts=db.get_company_contacts(company_id),
        cascade=db.get_company_cascade_counts(company_id),
    )


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def companies_edit(company_id):
    company = db.get_company(company_id) or abort(404)
    if request.method == "POST":
        data, errors = validate_company(request.form)
        if not errors:
            db.update_company(company_id, data)
            flash(f"Updated {data['company_name']}.", "success")
            return redirect(url_for("companies_detail", company_id=company_id))
        for error in errors:
            flash(error, "error")
        return render_template("company_form.html", form=request.form, company=company), 400
    return render_template("company_form.html", form=company, company=company)


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def companies_delete(company_id):
    company = db.get_company(company_id) or abort(404)
    also_removed = cascade_message(db.get_company_cascade_counts(company_id))
    db.delete_company(company_id)
    message = f"Deleted {company['company_name']}"
    flash(f"{message} and {also_removed}." if also_removed else f"{message}.", "success")
    return redirect(url_for("companies"))


# ---------------------------------------------------------------------
# Placeholders until each section is built
# ---------------------------------------------------------------------

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
