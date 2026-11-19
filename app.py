"""Job Application Tracker - Flask application (routes, validation, rendering).

All SQL lives in database.py; this module only handles HTTP concerns.

Endpoint names follow "<section>_<action>" (e.g. companies_edit) so the
nav bar can highlight the section a page belongs to.
"""
import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

import database as db
from matching import match_jobs
from validators import (INTERVIEW_TYPES, JOB_TYPES, STATUSES, parse_int, parse_skills, read_rounds,
                        validate_application, validate_company, validate_contact, validate_job)

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
app.jinja_env.globals["JOB_TYPES"] = JOB_TYPES
app.jinja_env.globals["STATUSES"] = STATUSES
app.jinja_env.globals["INTERVIEW_TYPES"] = INTERVIEW_TYPES


def next_round(application):
    """The earliest interview round dated today or later, or None."""
    today = date.today().isoformat()
    upcoming = [r for r in application["interview_data"]["rounds"] if r["date"] >= today]
    return min(upcoming, key=lambda r: r["date"]) if upcoming else None


app.jinja_env.globals["next_round"] = next_round


def flash_errors(errors):
    for error in errors:
        flash(error, "error")


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

# Statuses that mean the company responded. "Applied" means no response yet,
# and "Withdrawn" was the applicant's choice, not a response.
RESPONDED_STATUSES = ("Screening", "Interview", "Offer", "Rejected")


def response_rate(status_counts):
    """(responded, total) from a {status: count} dict."""
    total = sum(status_counts.values())
    responded = sum(status_counts.get(s, 0) for s in RESPONDED_STATUSES)
    return responded, total


@app.template_filter("percent")
def percent(part, total):
    """'63%' for 5 of 8, or '—' when total is 0.

    Rounds halves up (62.5 -> 63); Python's round() and Jinja's round filter
    round halves to even (62.5 -> 62), which surprises readers.
    """
    return f"{int(100 * part / total + 0.5)}%" if total else "—"


@app.route("/")
def dashboard():
    status_counts = db.get_status_counts()
    responded, total = response_rate(status_counts)
    return render_template(
        "dashboard.html",
        counts=db.get_table_counts(),
        # Every status in ENUM order, including those with zero applications.
        statuses=[(s, status_counts.get(s, 0)) for s in STATUSES],
        responded=responded,
        total=total,
        recent=db.get_applications(limit=5),
        upcoming=db.get_upcoming_interviews(),
    )


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
        flash_errors(errors)
        return render_template("company_form.html", form=request.form, company=None), 400
    return render_template("company_form.html", form={}, company=None)


@app.route("/companies/<int:company_id>")
def companies_detail(company_id):
    company = db.get_company(company_id) or abort(404)
    return render_template(
        "company_detail.html",
        company=company,
        jobs=db.get_jobs(company_id=company_id),
        contacts=db.get_contacts(company_id=company_id),
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
        flash_errors(errors)
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
# Jobs
# ---------------------------------------------------------------------

def job_form_values(job):
    """Flatten a job row into the form's field names (requirements JSON -> 3 fields)."""
    requirements = job["requirements"]
    return dict(
        job,
        skills=", ".join(requirements.get("skills", [])),
        experience_years=requirements.get("experience_years"),
        education=requirements.get("education"),
    )


def validate_job_form(form):
    """validate_job plus a check that the chosen company still exists."""
    data, errors = validate_job(form)
    if data["company_id"] is not None and db.get_company(data["company_id"]) is None:
        errors.append("The selected company no longer exists.")
    return data, errors


def render_job_form(form, job=None, status=200):
    return render_template("job_form.html", form=form, job=job,
                           companies=db.get_company_options()), status


@app.route("/jobs")
def jobs():
    # Unknown filter values are ignored rather than treated as errors.
    company_id = parse_int(request.args.get("company_id") or "")
    job_type = request.args.get("job_type")
    if job_type not in JOB_TYPES:
        job_type = None
    return render_template(
        "jobs.html",
        jobs=db.get_jobs(company_id=company_id, job_type=job_type),
        companies=db.get_company_options(),
        selected_company_id=company_id,
        selected_job_type=job_type,
    )


@app.route("/jobs/new", methods=["GET", "POST"])
def jobs_new():
    if request.method == "POST":
        data, errors = validate_job_form(request.form)
        if not errors:
            job_id = db.create_job(data)
            flash(f"Added {data['job_title']}.", "success")
            return redirect(url_for("jobs_detail", job_id=job_id))
        flash_errors(errors)
        return render_job_form(request.form, status=400)
    # ?company_id=N pre-selects the company (from the company detail page).
    return render_job_form({"company_id": parse_int(request.args.get("company_id") or "")})


@app.route("/jobs/<int:job_id>")
def jobs_detail(job_id):
    job = db.get_job(job_id) or abort(404)
    return render_template(
        "job_detail.html",
        job=job,
        applications=db.get_job_applications(job_id),
        cascade=db.get_job_cascade_counts(job_id),
    )


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def jobs_edit(job_id):
    job = db.get_job(job_id) or abort(404)
    if request.method == "POST":
        data, errors = validate_job_form(request.form)
        if not errors:
            db.update_job(job_id, data)
            flash(f"Updated {data['job_title']}.", "success")
            return redirect(url_for("jobs_detail", job_id=job_id))
        flash_errors(errors)
        return render_job_form(request.form, job=job, status=400)
    return render_job_form(job_form_values(job), job=job)


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def jobs_delete(job_id):
    job = db.get_job(job_id) or abort(404)
    also_removed = cascade_message(db.get_job_cascade_counts(job_id))
    db.delete_job(job_id)
    message = f"Deleted {job['job_title']} at {job['company_name']}"
    flash(f"{message} and {also_removed}." if also_removed else f"{message}.", "success")
    return redirect(url_for("jobs"))


# ---------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------

def validate_application_form(form):
    """validate_application plus a check that the chosen job still exists.
    Returns (data, errors, job)."""
    data, errors = validate_application(form)
    job = db.get_job(data["job_id"]) if data["job_id"] is not None else None
    if data["job_id"] is not None and job is None:
        errors.append("The selected job no longer exists.")
    return data, errors, job


def render_application_form(form, rounds, application=None, status=200):
    return render_template("application_form.html", form=form, rounds=rounds,
                           application=application, jobs=db.get_job_options(),
                           today=date.today().isoformat()), status


@app.route("/applications")
def applications():
    status = request.args.get("status")
    if status not in STATUSES:
        status = None
    return render_template("applications.html", applications=db.get_applications(status),
                           selected_status=status)


@app.route("/applications/new", methods=["GET", "POST"])
def applications_new():
    if request.method == "POST":
        data, errors, job = validate_application_form(request.form)
        contact = None
        if request.form.get("add_contact"):
            contact, contact_errors = validate_contact(request.form, prefix="nc_")
            errors += [f"New contact: {e}" for e in contact_errors]
            if job is not None:
                contact["company_id"] = job["company_id"]
        if not errors:
            try:
                application_id = db.create_application(data, contact)
            except db.DatabaseError as error:
                # The transaction was rolled back: neither row was saved.
                app.logger.exception("Application + contact transaction failed")
                flash(f"Nothing was saved because the database rejected the request ({error.msg}).", "error")
            else:
                saved = f"Saved your application to {job['job_title']} at {job['company_name']}"
                flash(f"{saved} and added {contact['contact_name']} as a contact." if contact
                      else f"{saved}.", "success")
                return redirect(url_for("applications_detail", application_id=application_id))
        flash_errors(errors)
        return render_application_form(request.form, read_rounds(request.form), status=400)
    # ?job_id=N pre-selects the job (from the job detail page and Job Match).
    return render_application_form(
        {"job_id": parse_int(request.args.get("job_id") or ""),
         "application_date": date.today().isoformat(), "status": "Applied"},
        rounds=[],
    )


@app.route("/applications/<int:application_id>")
def applications_detail(application_id):
    application = db.get_application(application_id) or abort(404)
    return render_template("application_detail.html", application=application,
                           contacts=db.get_contacts(company_id=application["company_id"]))


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def applications_edit(application_id):
    application = db.get_application(application_id) or abort(404)
    if request.method == "POST":
        data, errors, job = validate_application_form(request.form)
        if not errors:
            db.update_application(application_id, data)
            flash(f"Updated your application to {job['job_title']} at {job['company_name']}.", "success")
            return redirect(url_for("applications_detail", application_id=application_id))
        flash_errors(errors)
        return render_application_form(request.form, read_rounds(request.form),
                                        application=application, status=400)
    return render_application_form(application, application["interview_data"]["rounds"],
                                   application=application)


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def applications_delete(application_id):
    application = db.get_application(application_id) or abort(404)
    db.delete_application(application_id)
    flash(f"Deleted your application to {application['job_title']} at "
          f"{application['company_name']}.", "success")
    return redirect(url_for("applications"))


# ---------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------

def validate_contact_form(form):
    """validate_contact plus the company dropdown."""
    data, errors = validate_contact(form)
    data["company_id"] = parse_int(form.get("company_id") or "")
    if data["company_id"] is None:
        errors.insert(0, "Please choose a company.")
    elif db.get_company(data["company_id"]) is None:
        errors.insert(0, "The selected company no longer exists.")
    return data, errors


def render_contact_form(form, contact=None, status=200):
    return render_template("contact_form.html", form=form, contact=contact,
                           companies=db.get_company_options()), status


@app.route("/contacts")
def contacts():
    company_id = parse_int(request.args.get("company_id") or "")
    return render_template("contacts.html", contacts=db.get_contacts(company_id=company_id),
                           companies=db.get_company_options(), selected_company_id=company_id)


@app.route("/contacts/new", methods=["GET", "POST"])
def contacts_new():
    if request.method == "POST":
        data, errors = validate_contact_form(request.form)
        if not errors:
            contact_id = db.create_contact(data)
            flash(f"Added {data['contact_name']}.", "success")
            return redirect(url_for("contacts_detail", contact_id=contact_id))
        flash_errors(errors)
        return render_contact_form(request.form, status=400)
    # ?company_id=N pre-selects the company (from the company detail page).
    return render_contact_form({"company_id": parse_int(request.args.get("company_id") or "")})


@app.route("/contacts/<int:contact_id>")
def contacts_detail(contact_id):
    contact = db.get_contact(contact_id) or abort(404)
    return render_template("contact_detail.html", contact=contact)


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def contacts_edit(contact_id):
    contact = db.get_contact(contact_id) or abort(404)
    if request.method == "POST":
        data, errors = validate_contact_form(request.form)
        if not errors:
            db.update_contact(contact_id, data)
            flash(f"Updated {data['contact_name']}.", "success")
            return redirect(url_for("contacts_detail", contact_id=contact_id))
        flash_errors(errors)
        return render_contact_form(request.form, contact=contact, status=400)
    return render_contact_form(contact, contact=contact)


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def contacts_delete(contact_id):
    contact = db.get_contact(contact_id) or abort(404)
    db.delete_contact(contact_id)
    flash(f"Deleted {contact['contact_name']} ({contact['company_name']}).", "success")
    return redirect(url_for("contacts"))


# ---------------------------------------------------------------------
# Job Match
# ---------------------------------------------------------------------

@app.route("/job-match")
def job_match():
    # GET so results have a shareable URL, e.g. /job-match?skills=Python,+SQL
    submitted = "skills" in request.args
    skills_text = (request.args.get("skills") or "").strip()
    skills = parse_skills(skills_text)
    error, results, job_count = None, [], 0
    if submitted and not skills:
        error = "Enter at least one skill, separated by commas (e.g. Python, SQL, Flask)."
    elif skills:
        jobs = db.get_jobs()
        job_count = len(jobs)
        results = match_jobs(skills, jobs)
    return render_template("job_match.html", skills_text=skills_text, skills=skills, error=error,
                           results=results, job_count=job_count), (400 if error else 200)


if __name__ == "__main__":
    app.run(debug=True)
