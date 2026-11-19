"""Unit tests for the Job Match algorithm (no database needed)."""
from matching import match_jobs


def job(job_id, title, skills):
    return {"job_id": job_id, "job_title": title, "requirements": {"skills": skills}}


SEED_JOBS = [
    job(1, "Software Developer", ["Python", "SQL", "Flask"]),
    job(2, "Frontend Developer", ["JavaScript", "React", "HTML", "CSS"]),
    job(4, "Data Analyst", ["Python", "SQL", "Tableau"]),
    job(5, "Data Engineer", ["Python", "SQL", "Spark", "Airflow", "AWS"]),
    job(10, "Database Administrator", ["MySQL", "SQL", "Linux", "Backup and Recovery"]),
]


def by_title(results):
    return {r["job"]["job_title"]: r for r in results}


def test_spec_example():
    """Python, SQL, Flask -> Software Developer 100%, Data Analyst 67% missing Tableau."""
    results = match_jobs(["Python", "SQL", "Flask"], SEED_JOBS)

    top, second = results[0], results[1]
    assert top["job"]["job_title"] == "Software Developer"
    assert top["percent"] == 100
    assert top["matched"] == ["Python", "SQL", "Flask"]
    assert top["missing"] == []

    assert second["job"]["job_title"] == "Data Analyst"
    assert round(second["percent"]) == 67
    assert second["matched"] == ["Python", "SQL"]
    assert second["missing"] == ["Tableau"]


def test_sorted_by_percent_descending():
    percents = [r["percent"] for r in match_jobs(["Python", "SQL", "Flask"], SEED_JOBS)]
    assert percents == sorted(percents, reverse=True)


def test_matching_is_case_insensitive_and_trimmed():
    results = match_jobs(["  python ", "sql", "FLASK"], SEED_JOBS)
    assert results[0]["job"]["job_title"] == "Software Developer"
    assert results[0]["percent"] == 100
    # Names are shown as the job spells them, not as the user typed them.
    assert results[0]["matched"] == ["Python", "SQL", "Flask"]


def test_zero_percent_jobs_are_hidden():
    titles = by_title(match_jobs(["Python", "SQL", "Flask"], SEED_JOBS))
    assert "Frontend Developer" not in titles


def test_jobs_without_skills_are_hidden():
    jobs = [job(1, "No skills listed", []), {"job_id": 2, "job_title": "No requirements", "requirements": {}}]
    assert match_jobs(["Python"], jobs) == []


def test_no_aliases():
    """'SQL' does not match 'MySQL'."""
    dba = by_title(match_jobs(["SQL"], SEED_JOBS))["Database Administrator"]
    assert dba["matched"] == ["SQL"]
    assert "MySQL" in dba["missing"]


def test_tie_broken_by_matched_count():
    jobs = [
        job(1, "A - one of two", ["Python", "Go"]),           # 1/2 = 50%
        job(2, "B - two of four", ["Python", "SQL", "Go", "Rust"]),  # 2/4 = 50%
    ]
    results = match_jobs(["Python", "SQL"], jobs)
    assert [r["percent"] for r in results] == [50, 50]
    assert results[0]["job"]["job_title"] == "B - two of four"


def test_duplicate_job_skills_counted_once():
    results = match_jobs(["python"], [job(1, "Dupes", ["Python", "python ", "SQL"])])
    assert results[0]["total"] == 2
    assert results[0]["percent"] == 50


def test_empty_user_skills_match_nothing():
    assert match_jobs([], SEED_JOBS) == []
    assert match_jobs(["  ", ""], SEED_JOBS) == []
