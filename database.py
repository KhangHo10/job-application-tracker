"""Database functions for the Job Application Tracker.

Every SQL statement in the project lives in this module. All queries are
parameterized (%s placeholders) to prevent SQL injection, and every
connection is closed in a finally block.
"""
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


def get_company_jobs(company_id):
    """Jobs at one company, with how many applications each has."""
    return _fetch_all(
        """SELECT j.*,
                  (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
           FROM jobs j
           WHERE j.company_id = %s
           ORDER BY j.job_title""",
        (company_id,),
    )


def get_company_contacts(company_id):
    return _fetch_all(
        "SELECT * FROM contacts WHERE company_id = %s ORDER BY contact_name",
        (company_id,),
    )
