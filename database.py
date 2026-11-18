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
