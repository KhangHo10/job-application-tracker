"""Unit tests for server-side form validation (no database needed)."""
from datetime import date, timedelta

from werkzeug.datastructures import MultiDict

from validators import (parse_date, parse_int, parse_skills, read_rounds, validate_application,
                        validate_company, validate_contact, validate_job)

TODAY = date.today()


def has_error(errors, text):
    return any(text in e for e in errors)


# ---- helpers ----------------------------------------------------------

def test_parse_skills_trims_drops_blanks_and_dedupes():
    assert parse_skills(" Python, sql , PYTHON, ,Docker ") == ["Python", "sql", "Docker"]
    assert parse_skills("") == []
    assert parse_skills(None) == []


def test_parse_int_allows_commas():
    assert parse_int("80,000") == 80000
    assert parse_int("abc") is None
    assert parse_int("1.5") is None


def test_parse_date():
    assert parse_date("2026-01-31") == date(2026, 1, 31)
    assert parse_date("2026-02-30") is None
    assert parse_date("") is None


# ---- companies --------------------------------------------------------

def test_company_name_required():
    _, errors = validate_company({"company_name": "   "})
    assert has_error(errors, "Company name is required")


def test_company_blank_optional_fields_become_none():
    data, errors = validate_company({"company_name": "TechCorp", "industry": " ", "notes": ""})
    assert errors == []
    assert data["industry"] is None and data["notes"] is None


def test_company_website_gets_https_and_is_validated():
    data, errors = validate_company({"company_name": "A", "website": "www.example.com"})
    assert errors == [] and data["website"] == "https://www.example.com"
    _, errors = validate_company({"company_name": "A", "website": "not a url"})
    assert has_error(errors, "Website must be a valid URL")


def test_company_name_max_length():
    _, errors = validate_company({"company_name": "x" * 101})
    assert has_error(errors, "at most 100 characters")


# ---- jobs -------------------------------------------------------------

def valid_job(**overrides):
    form = {"company_id": "1", "job_title": "Developer", "job_type": "Full-time"}
    form.update(overrides)
    return form


def test_job_minimal_valid():
    data, errors = validate_job(valid_job())
    assert errors == []
    assert data["requirements"] == {"skills": [], "experience_years": None, "education": None}


def test_job_salary_min_must_not_exceed_max():
    _, errors = validate_job(valid_job(salary_min="90000", salary_max="80000"))
    assert has_error(errors, "Minimum salary cannot be greater than maximum salary")
    _, errors = validate_job(valid_job(salary_min="80,000", salary_max="80000"))
    assert errors == []


def test_job_salary_must_be_whole_non_negative_number():
    _, errors = validate_job(valid_job(salary_min="lots"))
    assert has_error(errors, "Minimum salary must be a whole number")
    _, errors = validate_job(valid_job(salary_max="-5"))
    assert has_error(errors, "Maximum salary cannot be less than 0")


def test_job_type_must_be_in_enum():
    _, errors = validate_job(valid_job(job_type="Gig"))
    assert has_error(errors, "Job type must be one of")


def test_job_required_fields():
    _, errors = validate_job({"job_type": "Full-time"})
    assert has_error(errors, "Please choose a company")
    assert has_error(errors, "Job title is required")


def test_job_date_posted_cannot_be_future():
    _, errors = validate_job(valid_job(date_posted=(TODAY + timedelta(days=1)).isoformat()))
    assert has_error(errors, "cannot be in the future")
    _, errors = validate_job(valid_job(date_posted="2026-99-99"))
    assert has_error(errors, "valid date")


def test_job_requirements_built_from_fields():
    data, errors = validate_job(valid_job(skills="Python, SQL", experience_years="2", education="BS"))
    assert errors == []
    assert data["requirements"] == {"skills": ["Python", "SQL"], "experience_years": 2, "education": "BS"}


def test_job_url_validated():
    data, errors = validate_job(valid_job(job_url="example.com/jobs/1"))
    assert errors == [] and data["job_url"] == "https://example.com/jobs/1"
    _, errors = validate_job(valid_job(job_url="nope"))
    assert has_error(errors, "Job posting URL must be a valid URL")


# ---- applications -----------------------------------------------------

def app_form(**overrides):
    form = MultiDict({"job_id": "1", "application_date": TODAY.isoformat(), "status": "Applied"})
    for key, value in overrides.items():
        if isinstance(value, list):
            form.setlist(key, value)
        else:
            form[key] = value
    return form


def test_application_minimal_valid():
    data, errors = validate_application(app_form())
    assert errors == []
    assert data["cover_letter_sent"] is False
    assert data["interview_data"] is None


def test_application_status_must_be_in_enum():
    _, errors = validate_application(app_form(status="Offer Received"))
    assert has_error(errors, "Status must be one of")


def test_application_date_required_and_not_future():
    _, errors = validate_application(app_form(application_date=""))
    assert has_error(errors, "Application date is required")
    _, errors = validate_application(app_form(application_date=(TODAY + timedelta(days=1)).isoformat()))
    assert has_error(errors, "cannot be in the future")


def test_rounds_blank_rows_dropped_even_with_type_selected():
    form = app_form(round_date=["", "2026-12-01"], round_type=["Technical", "Onsite"],
                    round_interviewer=["", "Panel"], round_notes=["", ""])
    assert len(read_rounds(form)) == 1


def test_rounds_sorted_by_date_and_stored_as_json_shape():
    form = app_form(round_date=["2026-12-10", "2026-12-01"], round_type=["Onsite", "Phone Screen"],
                    round_interviewer=["Panel", "Rec"], round_notes=["", "first"])
    data, errors = validate_application(form)
    assert errors == []
    assert data["interview_data"] == {"rounds": [
        {"date": "2026-12-01", "type": "Phone Screen", "interviewer": "Rec", "notes": "first"},
        {"date": "2026-12-10", "type": "Onsite", "interviewer": "Panel", "notes": ""},
    ]}


def test_round_needs_valid_date_and_type():
    form = app_form(round_date=["2026-13-40"], round_type=["Pizza"], round_interviewer=["Bob"], round_notes=[""])
    _, errors = validate_application(form)
    assert has_error(errors, "Interview round 1 needs a valid date")
    assert has_error(errors, "Interview round 1 type must be one of")


# ---- contacts ---------------------------------------------------------

def test_contact_name_required_and_email_format():
    _, errors = validate_contact({"contact_name": "", "email": "a@b"})
    assert has_error(errors, "Contact name is required")
    assert has_error(errors, "Email must be a valid address")
    _, errors = validate_contact({"contact_name": "Ann", "email": "ann@example.com"})
    assert errors == []


def test_contact_phone_format():
    _, errors = validate_contact({"contact_name": "Ann", "phone": "+1 (305) 555.0100"})
    assert errors == []
    _, errors = validate_contact({"contact_name": "Ann", "phone": "12"})
    assert has_error(errors, "Phone must contain at least 7 digits")
    _, errors = validate_contact({"contact_name": "Ann", "phone": "call me 5550100"})
    assert has_error(errors, "Phone must")


def test_contact_prefix_reads_embedded_fields():
    data, errors = validate_contact({"nc_contact_name": "Ann", "nc_title": "Recruiter"}, prefix="nc_")
    assert errors == []
    assert data["contact_name"] == "Ann" and data["title"] == "Recruiter"
