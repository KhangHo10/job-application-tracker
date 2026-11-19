"""Smoke test: every page loads against the real database.

Read-only (GET requests only), so it never changes your data. Skipped
automatically when MySQL is not reachable, e.g. before .env is set up.
"""
import pytest

import database as db
from app import app

try:
    db.get_db().close()
except db.DatabaseError as error:
    pytest.skip(f"MySQL not reachable ({error}); skipping route smoke tests.", allow_module_level=True)


@pytest.fixture
def client():
    return app.test_client()


def first_id(rows, key):
    if not rows:
        pytest.skip(f"no rows to test {key} detail pages")
    return rows[0][key]


@pytest.mark.parametrize("path", [
    "/",
    "/companies", "/companies?q=tech", "/companies/new",
    "/jobs", "/jobs?company_id=1&job_type=Full-time", "/jobs/new",
    "/applications", "/applications?status=Interview", "/applications/new",
    "/contacts", "/contacts?company_id=1", "/contacts/new",
    "/job-match", "/job-match?skills=Python,+SQL,+Flask",
])
def test_list_and_form_pages_load(client, path):
    assert client.get(path).status_code == 200


def test_detail_and_edit_pages_load(client):
    pages = [
        ("companies", first_id(db.get_companies(), "company_id")),
        ("jobs", first_id(db.get_jobs(), "job_id")),
        ("applications", first_id(db.get_applications(), "application_id")),
        ("contacts", first_id(db.get_contacts(), "contact_id")),
    ]
    for section, row_id in pages:
        assert client.get(f"/{section}/{row_id}").status_code == 200
        assert client.get(f"/{section}/{row_id}/edit").status_code == 200


def test_missing_rows_return_404(client):
    for section in ("companies", "jobs", "applications", "contacts"):
        assert client.get(f"/{section}/999999999").status_code == 404


def test_delete_requires_post(client):
    assert client.get("/companies/1/delete").status_code == 405


def test_job_match_empty_input_shows_validation_message(client):
    response = client.get("/job-match?skills=+,+")
    assert response.status_code == 400
    assert b"Enter at least one skill" in response.data
