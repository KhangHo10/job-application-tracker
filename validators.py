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

# Must match the ENUM in schema.sql.
JOB_TYPES = ("Full-time", "Part-time", "Contract", "Internship")


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


def parse_skills(text):
    """Split 'Python, SQL,  python ,' into ['Python', 'SQL'].

    Trims whitespace, drops blanks, and removes case-insensitive duplicates
    (keeping the first spelling).
    """
    skills, seen = [], set()
    for raw in (text or "").split(","):
        skill = raw.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def _optional_int(form, field, label, errors, minimum=0, maximum=None):
    """Parse an optional whole-number field, adding an error if it is invalid."""
    text = clean_text(form, field)
    if text is None:
        return None
    value = parse_int(text)
    if value is None:
        errors.append(f"{label} must be a whole number.")
    elif value < minimum:
        errors.append(f"{label} cannot be less than {minimum}.")
    elif maximum is not None and value > maximum:
        errors.append(f"{label} cannot be more than {maximum}.")
    else:
        return value
    return None


def _optional_date(form, field, label, errors, allow_future=True):
    text = clean_text(form, field)
    if text is None:
        return None
    value = parse_date(text)
    if value is None:
        errors.append(f"{label} must be a valid date (YYYY-MM-DD).")
    elif not allow_future and value > date.today():
        errors.append(f"{label} cannot be in the future.")
    return value


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


def validate_job(form):
    """Validate the job form. The skills/experience/education fields are
    combined into data["requirements"], the dict stored in the JSON column."""
    errors = []
    data = {
        "company_id": parse_int(form.get("company_id") or ""),
        "job_title": clean_text(form, "job_title"),
        "job_type": clean_text(form, "job_type"),
        "salary_min": _optional_int(form, "salary_min", "Minimum salary", errors),
        "salary_max": _optional_int(form, "salary_max", "Maximum salary", errors),
        "job_url": normalize_url(clean_text(form, "job_url")),
        "date_posted": _optional_date(form, "date_posted", "Date posted", errors, allow_future=False),
    }

    if data["company_id"] is None:
        errors.append("Please choose a company.")
    check_required(data["job_title"], "Job title", errors)
    check_max_length(data["job_title"], 100, "Job title", errors)
    if data["job_type"] not in JOB_TYPES:
        errors.append(f"Job type must be one of: {', '.join(JOB_TYPES)}.")

    if (data["salary_min"] is not None and data["salary_max"] is not None
            and data["salary_min"] > data["salary_max"]):
        errors.append("Minimum salary cannot be greater than maximum salary.")

    if data["job_url"] is not None:
        if not is_valid_url(data["job_url"]):
            errors.append("Job posting URL must be a valid URL, e.g. https://example.com/jobs/123.")
        check_max_length(data["job_url"], 300, "Job posting URL", errors)

    skills = parse_skills(form.get("skills"))
    for skill in skills:
        check_max_length(skill, 50, f'Skill "{skill[:20]}…"', errors)
    education = clean_text(form, "education")
    check_max_length(education, 100, "Education", errors)
    data["requirements"] = {
        "skills": skills,
        "experience_years": _optional_int(form, "experience_years", "Years of experience",
                                          errors, maximum=50),
        "education": education,
    }

    return data, errors
