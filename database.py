"""Database functions for the Job Application Tracker.

Every SQL statement in the project lives in this module. All queries are
parameterized (%s placeholders) to prevent SQL injection, and every
connection is closed in a finally block.
"""
import json
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Re-exported so app.py can catch database errors without importing the driver.
DatabaseError = mysql.connector.Error


def get_db():
    """Open a new connection using the settings in .env."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "job_tracker"),
    )


# ---------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------

def _fetch_all(sql, params=()):
    """Run a SELECT and return every row as a dict."""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def _fetch_one(sql, params=()):
    """Run a SELECT and return the first row as a dict, or None."""
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _insert(sql, params=()):
    """Run an INSERT, commit, and return the new row's id."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    except DatabaseError:
        conn.rollback()
        raise
    finally:
        conn.close()


def _load_json(rows, column, default):
    """Decode a JSON column in place (the driver returns it as a string)."""
    for row in rows:
        value = row.get(column)
        row[column] = json.loads(value) if value else default()
    return rows


def _like(term):
    """Wrap a search term for LIKE, escaping the % and _ wildcards."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _execute(sql, params=()):
    """Run an UPDATE or DELETE, commit, and return the affected row count."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    except DatabaseError:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------

COMPANY_FIELDS = ("company_name", "industry", "website", "city", "state", "notes")


def get_companies(search=None):
    """All companies with job/contact counts, optionally filtered by a search term."""
    sql = """
        SELECT c.*,
               (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id) AS job_count,
               (SELECT COUNT(*) FROM contacts ct WHERE ct.company_id = c.company_id) AS contact_count,
               (SELECT COUNT(*) FROM applications a
                    JOIN jobs j ON a.job_id = j.job_id
                 WHERE j.company_id = c.company_id) AS application_count
        FROM companies c
    """
    params = ()
    if search:
        sql += """
        WHERE c.company_name LIKE %s OR c.industry LIKE %s
           OR c.city LIKE %s OR c.state LIKE %s
        """
        params = (_like(search),) * 4
    sql += " ORDER BY c.company_name, c.company_id"
    return _fetch_all(sql, params)


def get_company(company_id):
    return _fetch_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))


def get_company_options():
    """(id, name, city) for every company, for <select> dropdowns."""
    return _fetch_all(
        "SELECT company_id, company_name, city FROM companies ORDER BY company_name, company_id"
    )


def create_company(data):
    return _insert(
        """INSERT INTO companies (company_name, industry, website, city, state, notes)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        tuple(data[f] for f in COMPANY_FIELDS),
    )


def update_company(company_id, data):
    return _execute(
        """UPDATE companies
           SET company_name = %s, industry = %s, website = %s,
               city = %s, state = %s, notes = %s
           WHERE company_id = %s""",
        tuple(data[f] for f in COMPANY_FIELDS) + (company_id,),
    )


def get_company_cascade_counts(company_id):
    """How many rows ON DELETE CASCADE will remove along with this company."""
    return _fetch_one(
        """SELECT
               (SELECT COUNT(*) FROM jobs WHERE company_id = %s) AS job_count,
               (SELECT COUNT(*) FROM applications a JOIN jobs j ON a.job_id = j.job_id
                 WHERE j.company_id = %s) AS application_count,
               (SELECT COUNT(*) FROM contacts WHERE company_id = %s) AS contact_count""",
        (company_id,) * 3,
    )


def delete_company(company_id):
    """Delete a company; its jobs, their applications, and its contacts cascade."""
    return _execute("DELETE FROM companies WHERE company_id = %s", (company_id,))


# ---------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------

JOB_FIELDS = ("company_id", "job_title", "job_type", "salary_min", "salary_max",
              "job_url", "date_posted")

_JOB_SELECT = """
    SELECT j.*, c.company_name,
           (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
    FROM jobs j
    JOIN companies c ON c.company_id = j.company_id
"""


def get_jobs(company_id=None, job_type=None):
    """All jobs with company name and application count, optionally filtered."""
    conditions, params = [], []
    if company_id is not None:
        conditions.append("j.company_id = %s")
        params.append(company_id)
    if job_type is not None:
        conditions.append("j.job_type = %s")
        params.append(job_type)
    sql = _JOB_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY c.company_name, j.job_title, j.job_id"
    return _load_json(_fetch_all(sql, tuple(params)), "requirements", dict)


def get_job(job_id):
    rows = _fetch_all(_JOB_SELECT + " WHERE j.job_id = %s", (job_id,))
    return _load_json(rows, "requirements", dict)[0] if rows else None


def get_job_options():
    """Job id, title, and company for every job, for <select> dropdowns."""
    return _fetch_all(
        """SELECT j.job_id, j.job_title, c.company_name
           FROM jobs j JOIN companies c ON c.company_id = j.company_id
           ORDER BY c.company_name, j.job_title, j.job_id"""
    )


def create_job(data):
    return _insert(
        """INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                             job_url, date_posted, requirements)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        tuple(data[f] for f in JOB_FIELDS) + (json.dumps(data["requirements"]),),
    )


def update_job(job_id, data):
    return _execute(
        """UPDATE jobs
           SET company_id = %s, job_title = %s, job_type = %s, salary_min = %s,
               salary_max = %s, job_url = %s, date_posted = %s, requirements = %s
           WHERE job_id = %s""",
        tuple(data[f] for f in JOB_FIELDS) + (json.dumps(data["requirements"]), job_id),
    )


def get_job_cascade_counts(job_id):
    """How many rows ON DELETE CASCADE will remove along with this job."""
    return _fetch_one(
        "SELECT COUNT(*) AS application_count FROM applications WHERE job_id = %s",
        (job_id,),
    )


def delete_job(job_id):
    """Delete a job; its applications cascade."""
    return _execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))


def get_job_applications(job_id):
    return _fetch_all(
        """SELECT * FROM applications
           WHERE job_id = %s
           ORDER BY application_date DESC, application_id DESC""",
        (job_id,),
    )


# ---------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------

APPLICATION_FIELDS = ("job_id", "application_date", "status", "resume_version", "cover_letter_sent")

_APPLICATION_SELECT = """
    SELECT a.*, j.job_title, j.company_id, c.company_name
    FROM applications a
    JOIN jobs j ON j.job_id = a.job_id
    JOIN companies c ON c.company_id = j.company_id
"""


def _empty_rounds():
    return {"rounds": []}


def _application_params(data):
    interview_data = json.dumps(data["interview_data"]) if data["interview_data"] else None
    return tuple(data[f] for f in APPLICATION_FIELDS) + (interview_data,)


def get_applications(status=None, limit=None):
    """Applications with job and company names, newest first, optionally by status."""
    sql, params = _APPLICATION_SELECT, ()
    if status is not None:
        sql += " WHERE a.status = %s"
        params = (status,)
    sql += " ORDER BY a.application_date DESC, a.application_id DESC"
    if limit is not None:
        sql += " LIMIT %s"
        params += (limit,)
    return _load_json(_fetch_all(sql, params), "interview_data", _empty_rounds)


def get_application(application_id):
    rows = _fetch_all(_APPLICATION_SELECT + " WHERE a.application_id = %s", (application_id,))
    return _load_json(rows, "interview_data", _empty_rounds)[0] if rows else None


def create_application(data, contact=None):
    """Insert an application, and optionally a contact, in ONE transaction.

    If `contact` is given (a dict with company_id and the contact fields),
    both rows are inserted together: if either INSERT fails, ROLLBACK undoes
    both, so we never save an application without its contact or vice versa.
    Returns the new application_id.
    """
    conn = get_db()
    try:
        conn.start_transaction()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO applications (job_id, application_date, status, resume_version,
                                         cover_letter_sent, interview_data)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            _application_params(data),
        )
        application_id = cursor.lastrowid
        if contact is not None:
            cursor.execute(
                """INSERT INTO contacts (company_id, contact_name, title, email, phone,
                                         linkedin_url, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                tuple(contact[f] for f in ("company_id",) + CONTACT_FIELDS),
            )
        conn.commit()
        return application_id
    except DatabaseError:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_application(application_id, data):
    return _execute(
        """UPDATE applications
           SET job_id = %s, application_date = %s, status = %s, resume_version = %s,
               cover_letter_sent = %s, interview_data = %s
           WHERE application_id = %s""",
        _application_params(data) + (application_id,),
    )


def delete_application(application_id):
    return _execute("DELETE FROM applications WHERE application_id = %s", (application_id,))


# ---------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------

CONTACT_FIELDS = ("contact_name", "title", "email", "phone", "linkedin_url", "notes")

_CONTACT_SELECT = """
    SELECT ct.*, c.company_name
    FROM contacts ct
    JOIN companies c ON c.company_id = ct.company_id
"""


def get_contacts(company_id=None):
    """All contacts with company name, optionally for one company."""
    sql, params = _CONTACT_SELECT, ()
    if company_id is not None:
        sql += " WHERE ct.company_id = %s"
        params = (company_id,)
    sql += " ORDER BY ct.contact_name, ct.contact_id"
    return _fetch_all(sql, params)


def get_contact(contact_id):
    return _fetch_one(_CONTACT_SELECT + " WHERE ct.contact_id = %s", (contact_id,))


def create_contact(data):
    return _insert(
        """INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        tuple(data[f] for f in ("company_id",) + CONTACT_FIELDS),
    )


def update_contact(contact_id, data):
    return _execute(
        """UPDATE contacts
           SET company_id = %s, contact_name = %s, title = %s, email = %s,
               phone = %s, linkedin_url = %s, notes = %s
           WHERE contact_id = %s""",
        tuple(data[f] for f in ("company_id",) + CONTACT_FIELDS) + (contact_id,),
    )


def delete_contact(contact_id):
    return _execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

def get_table_counts():
    return _fetch_one(
        """SELECT (SELECT COUNT(*) FROM companies) AS companies,
                  (SELECT COUNT(*) FROM jobs) AS jobs,
                  (SELECT COUNT(*) FROM applications) AS applications,
                  (SELECT COUNT(*) FROM contacts) AS contacts"""
    )


def get_status_counts():
    """{status: count} for statuses that have at least one application."""
    rows = _fetch_all("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
    return {row["status"]: row["n"] for row in rows}


def get_upcoming_interviews(limit=10):
    """Interview rounds dated today or later, soonest first.

    JSON_TABLE turns each application's interview_data.rounds array into
    rows, so the rounds can be filtered, joined, and sorted in SQL.
    """
    return _fetch_all(
        """SELECT a.application_id, a.status, j.job_title, c.company_name,
                  r.round_date, r.round_type, r.interviewer,
                  DATEDIFF(r.round_date, CURDATE()) AS days_until
           FROM applications a
           CROSS JOIN JSON_TABLE(
               a.interview_data, '$.rounds[*]'
               COLUMNS (
                   round_date  DATE         PATH '$.date',
                   round_type  VARCHAR(50)  PATH '$.type',
                   interviewer VARCHAR(100) PATH '$.interviewer'
               )
           ) AS r
           JOIN jobs j ON j.job_id = a.job_id
           JOIN companies c ON c.company_id = j.company_id
           WHERE r.round_date >= CURDATE()
           ORDER BY r.round_date, a.application_id
           LIMIT %s""",
        (limit,),
    )
