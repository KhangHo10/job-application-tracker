"""Job Match: rank jobs by how many of their required skills the user has.

    match % = (user skills ∩ job skills) / (number of job skills)

Matching is case-insensitive and ignores surrounding spaces ("python " ==
"Python"). There are no aliases, so "SQL" does not match "MySQL". Jobs with
no listed skills, or with no skills in common (0%), are left out.

Pure functions with no Flask or database imports, so they can be unit-tested.
"""


def _skill_key(skill):
    return skill.strip().lower()


def match_job(user_keys, job):
    """Score one job against a set of normalized user skills.

    Returns a dict with the job, matched/missing skill names (as the job
    spells them), and the counts; or None if the job lists no skills or none match.
    """
    # Unique job skills by key, keeping the job's spelling of each.
    skills = {}
    for skill in job["requirements"].get("skills") or []:
        key = _skill_key(skill)
        if key and key not in skills:
            skills[key] = skill.strip()
    if not skills:
        return None

    matched = [name for key, name in skills.items() if key in user_keys]
    if not matched:
        return None
    missing = [name for key, name in skills.items() if key not in user_keys]
    return {
        "job": job,
        "matched": matched,
        "missing": missing,
        "total": len(skills),
        "percent": 100 * len(matched) / len(skills),
    }


def match_jobs(user_skills, jobs):
    """Rank jobs for a list of user skills.

    Sorted by match % (highest first), then by number of matched skills,
    then by job title so ties are stable.
    """
    user_keys = {_skill_key(s) for s in user_skills if s.strip()}
    results = [r for r in (match_job(user_keys, job) for job in jobs) if r is not None]
    results.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["job"]["job_title"].lower()))
    return results
