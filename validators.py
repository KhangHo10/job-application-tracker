"""Server-side form validation.

Each validate_* function takes the submitted form (any mapping of field
name -> string, e.g. Flask's request.form) and returns (data, errors):
  data   - cleaned values ready for database.py (blank strings become None)
  errors - list of human-readable messages; empty when the form is valid

These are pure functions with no Flask or database imports so they can be
unit-tested on their own.
"""
import re
from datetime import date
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------

def clean_text(form, field):
    """Stripped string value, or None when missing or blank."""
    value = (form.get(field) or "").strip()
    return value or None


def check_required(value, label, errors):
    if value is None:
        errors.append(f"{label} is required.")


def check_max_length(value, max_len, label, errors):
    if value is not None and len(value) > max_len:
        errors.append(f"{label} must be at most {max_len} characters.")


def normalize_url(value):
    """Add https:// when the user typed a bare domain like www.example.com."""
    if value and "://" not in value:
        return "https://" + value
    return value


def is_valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and "." in parsed.netloc


def is_valid_email(value):
    return bool(EMAIL_RE.match(value))


def parse_date(value):
    """date from 'YYYY-MM-DD', or None if the string is not a valid date."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def parse_int(value):
    """int from a string (commas allowed, e.g. '80,000'), or None if not a whole number."""
    try:
        return int(value.replace(",", ""))
    except (AttributeError, ValueError):
        return None


# ---------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------

def validate_company(form):
    errors = []
    data = {
        "company_name": clean_text(form, "company_name"),
        "industry": clean_text(form, "industry"),
        "website": normalize_url(clean_text(form, "website")),
        "city": clean_text(form, "city"),
        "state": clean_text(form, "state"),
        "notes": clean_text(form, "notes"),
    }

    check_required(data["company_name"], "Company name", errors)
    check_max_length(data["company_name"], 100, "Company name", errors)
    check_max_length(data["industry"], 50, "Industry", errors)
    check_max_length(data["city"], 50, "City", errors)
    check_max_length(data["state"], 50, "State", errors)

    if data["website"] is not None:
        if not is_valid_url(data["website"]):
            errors.append("Website must be a valid URL, e.g. https://example.com.")
        check_max_length(data["website"], 200, "Website", errors)

    return data, errors
