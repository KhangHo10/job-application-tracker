DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE job_tracker;

CREATE TABLE companies (
    company_id    INT AUTO_INCREMENT PRIMARY KEY,
    company_name  VARCHAR(100) NOT NULL,       -- not UNIQUE: two companies may share a name
    industry      VARCHAR(50),
    website       VARCHAR(200),
    city          VARCHAR(50),
    state         VARCHAR(50),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE jobs (
    job_id        INT AUTO_INCREMENT PRIMARY KEY,
    company_id    INT NOT NULL,
    job_title     VARCHAR(100) NOT NULL,
    job_type      ENUM('Full-time', 'Part-time', 'Contract', 'Internship') NOT NULL DEFAULT 'Full-time',
    salary_min    INT,
    salary_max    INT,
    job_url       VARCHAR(300),
    date_posted   DATE,
    -- Shape: {"skills": ["Python", "SQL"], "experience_years": 2, "education": "Bachelor's"}
    requirements  JSON,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies (company_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_salary_range
        CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);

CREATE TABLE applications (
    application_id    INT AUTO_INCREMENT PRIMARY KEY,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn')
                      NOT NULL DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN NOT NULL DEFAULT FALSE,
    -- Shape: {"rounds": [{"date": "YYYY-MM-DD", "type": "...", "interviewer": "...", "notes": "..."}]}
    interview_data    JSON,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES jobs (job_id)
        ON DELETE CASCADE
);

-- Column names follow the project spec (contact_name, title) rather than
-- Assignment 4's first_name / last_name / job_title.
CREATE TABLE contacts (
    contact_id    INT AUTO_INCREMENT PRIMARY KEY,
    company_id    INT NOT NULL,
    contact_name  VARCHAR(100) NOT NULL,
    title         VARCHAR(100),
    email         VARCHAR(100),
    phone         VARCHAR(30),
    linkedin_url  VARCHAR(200),
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_contacts_company
        FOREIGN KEY (company_id) REFERENCES companies (company_id)
        ON DELETE CASCADE
);

-- Speeds up job title searches and ORDER BY job_title on the Jobs page.
CREATE INDEX idx_job_title ON jobs (job_title);

-- Composite index for the Jobs page filter (company + job type). Because
-- company_id is the leftmost column, it also serves the fk_jobs_company
-- foreign key, so MySQL does not need a separate index for it.
CREATE INDEX idx_company_type ON jobs (company_id, job_type);

-- Speeds up the Applications status filter and the dashboard's
-- applications-by-status counts.
CREATE INDEX idx_app_status ON applications (status);

-- Speeds up grouping and filtering companies by industry.
CREATE INDEX idx_company_industry ON companies (industry);

-- (idx_salary was dropped in Assignment 3: salary ranges are rarely
-- searched, so the index cost more on writes than it saved on reads.)

-- All dates are relative to CURDATE() so the dashboard always shows
-- recent applications and upcoming interviews.
INSERT INTO companies (company_id, company_name, industry, website, city, state, notes) VALUES
(1, 'TechCorp',          'Technology',     'https://techcorp.example.com',    'Miami',    'FL', 'Mid-size software company; strong internship program.'),
(2, 'DataCo',            'Data Analytics', 'https://dataco.example.com',      'Austin',   'TX', 'Analytics consultancy with mostly remote teams.'),
(3, 'CloudNine Systems', 'Cloud Computing','https://cloudnine.example.com',   'Seattle',  'WA', NULL),
(4, 'HealthBridge',      'Healthcare',     'https://healthbridge.example.com','Orlando',  'FL', 'Hospital network; IT department is growing.'),
(5, 'FinEdge Capital',   'Finance',        'https://finedge.example.com',     'New York', 'NY', 'Hybrid schedule, 3 days in office.');

-- With the skills "Python, SQL, Flask", Job Match should rank
-- Software Developer @ TechCorp at 100% (3/3) and
-- Data Analyst @ DataCo at 67% (2/3, missing Tableau).
-- Every other job scores 40% or less.
INSERT INTO jobs (job_id, company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1,  1, 'Software Developer',              'Full-time',  80000, 105000, 'https://techcorp.example.com/careers/101',  DATE_SUB(CURDATE(), INTERVAL 30 DAY),
     '{"skills": ["Python", "SQL", "Flask"], "experience_years": 2, "education": "Bachelor''s in Computer Science"}'),
(2,  1, 'Frontend Developer',              'Full-time',  70000,  95000, 'https://techcorp.example.com/careers/102',  DATE_SUB(CURDATE(), INTERVAL 35 DAY),
     '{"skills": ["JavaScript", "React", "HTML", "CSS"], "experience_years": 1, "education": "Bachelor''s"}'),
(3,  1, 'Software Engineering Intern',     'Internship', 40000,  48000, 'https://techcorp.example.com/careers/103',  DATE_SUB(CURDATE(), INTERVAL 10 DAY),
     '{"skills": ["Java", "Git", "Python", "Agile"], "experience_years": 0, "education": "Pursuing Bachelor''s"}'),
(4,  2, 'Data Analyst',                    'Full-time',  65000,  85000, 'https://dataco.example.com/jobs/data-analyst', DATE_SUB(CURDATE(), INTERVAL 21 DAY),
     '{"skills": ["Python", "SQL", "Tableau"], "experience_years": 1, "education": "Bachelor''s in Statistics or related"}'),
(5,  2, 'Data Engineer',                   'Full-time',  95000, 125000, 'https://dataco.example.com/jobs/data-engineer', DATE_SUB(CURDATE(), INTERVAL 40 DAY),
     '{"skills": ["Python", "SQL", "Spark", "Airflow", "AWS"], "experience_years": 3, "education": "Bachelor''s"}'),
(6,  2, 'Business Intelligence Analyst',   'Contract',   60000,  80000, 'https://dataco.example.com/jobs/bi-analyst', DATE_SUB(CURDATE(), INTERVAL 14 DAY),
     '{"skills": ["SQL", "Power BI", "Excel"], "experience_years": 2, "education": "Bachelor''s"}'),
(7,  3, 'Cloud Engineer',                  'Full-time', 100000, 135000, 'https://cloudnine.example.com/careers/cloud-engineer', DATE_SUB(CURDATE(), INTERVAL 12 DAY),
     '{"skills": ["AWS", "Docker", "Kubernetes", "Terraform"], "experience_years": 3, "education": "Bachelor''s"}'),
(8,  3, 'DevOps Engineer',                 'Full-time',  95000, 130000, 'https://cloudnine.example.com/careers/devops', DATE_SUB(CURDATE(), INTERVAL 18 DAY),
     '{"skills": ["Linux", "Docker", "Jenkins", "Python", "Bash"], "experience_years": 2, "education": "Bachelor''s"}'),
(9,  3, 'Backend Developer',               'Contract',   85000, 110000, 'https://cloudnine.example.com/careers/backend', DATE_SUB(CURDATE(), INTERVAL 7 DAY),
     '{"skills": ["Java", "Spring Boot", "SQL", "Docker"], "experience_years": 2, "education": "Bachelor''s"}'),
(10, 4, 'Database Administrator',          'Full-time',  75000, 100000, 'https://healthbridge.example.com/careers/dba', DATE_SUB(CURDATE(), INTERVAL 9 DAY),
     '{"skills": ["MySQL", "SQL", "Linux", "Backup and Recovery"], "experience_years": 3, "education": "Bachelor''s"}'),
(11, 4, 'IT Support Specialist',           'Part-time',  35000,  45000, 'https://healthbridge.example.com/careers/it-support', DATE_SUB(CURDATE(), INTERVAL 5 DAY),
     '{"skills": ["Windows", "Active Directory", "Networking"], "experience_years": 0, "education": "Associate''s or certification"}'),
(12, 5, 'Quantitative Analyst',            'Full-time', 110000, 150000, 'https://finedge.example.com/careers/quant', DATE_SUB(CURDATE(), INTERVAL 50 DAY),
     '{"skills": ["Python", "R", "Statistics", "SQL", "Excel"], "experience_years": 2, "education": "Master''s in a quantitative field"}');

-- Interview round dates are built with DATE_FORMAT(DATE_ADD(...)) so they
-- are stored as plain "YYYY-MM-DD" strings inside the JSON.
INSERT INTO applications (application_id, job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, 1,  DATE_SUB(CURDATE(), INTERVAL 20 DAY), 'Interview', 'v3-software', TRUE,
    JSON_OBJECT('rounds', JSON_ARRAY(
        JSON_OBJECT('date', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '%Y-%m-%d'),
                    'type', 'Phone Screen', 'interviewer', 'Maria Lopez', 'notes', 'Went well; moving to technical round.'),
        JSON_OBJECT('date', DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '%Y-%m-%d'),
                    'type', 'Technical', 'interviewer', 'James Carter', 'notes', 'Review Flask and SQL joins.')
    ))),
(2, 4,  DATE_SUB(CURDATE(), INTERVAL 15 DAY), 'Screening', 'v2-data', FALSE,
    JSON_OBJECT('rounds', JSON_ARRAY(
        JSON_OBJECT('date', DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '%Y-%m-%d'),
                    'type', 'Phone Screen', 'interviewer', 'Priya Shah', 'notes', 'Recruiter call.')
    ))),
(3, 5,  DATE_SUB(CURDATE(), INTERVAL 30 DAY), 'Rejected', 'v2-data', TRUE,
    JSON_OBJECT('rounds', JSON_ARRAY(
        JSON_OBJECT('date', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 22 DAY), '%Y-%m-%d'),
                    'type', 'Phone Screen', 'interviewer', 'Priya Shah', 'notes', 'Wanted more Spark experience.')
    ))),
(4, 7,  DATE_SUB(CURDATE(), INTERVAL 8 DAY),  'Applied', 'v3-software', FALSE, NULL),
(5, 12, DATE_SUB(CURDATE(), INTERVAL 40 DAY), 'Offer', 'v2-data', TRUE,
    JSON_OBJECT('rounds', JSON_ARRAY(
        JSON_OBJECT('date', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 32 DAY), '%Y-%m-%d'),
                    'type', 'Phone Screen', 'interviewer', 'Daniel Kim', 'notes', ''),
        JSON_OBJECT('date', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 25 DAY), '%Y-%m-%d'),
                    'type', 'Technical', 'interviewer', 'Daniel Kim', 'notes', 'Probability and SQL questions.'),
        JSON_OBJECT('date', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 18 DAY), '%Y-%m-%d'),
                    'type', 'Onsite', 'interviewer', 'Hiring panel', 'notes', 'Offer received a week later.')
    ))),
(6, 10, DATE_SUB(CURDATE(), INTERVAL 5 DAY),  'Applied', 'v3-software', TRUE, NULL),
(7, 2,  DATE_SUB(CURDATE(), INTERVAL 25 DAY), 'Withdrawn', 'v1-frontend', FALSE, NULL),
(8, 8,  DATE_SUB(CURDATE(), INTERVAL 12 DAY), 'Interview', 'v3-software', TRUE,
    JSON_OBJECT('rounds', JSON_ARRAY(
        JSON_OBJECT('date', DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 4 DAY), '%Y-%m-%d'),
                    'type', 'Phone Screen', 'interviewer', 'Alex Nguyen', 'notes', ''),
        JSON_OBJECT('date', DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL 7 DAY), '%Y-%m-%d'),
                    'type', 'Onsite', 'interviewer', 'DevOps team', 'notes', 'Half-day onsite in Seattle.')
    )));

INSERT INTO contacts (contact_id, company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 1, 'Maria Lopez',  'Technical Recruiter',      'maria.lopez@techcorp.example.com',   '305-555-0142', 'https://www.linkedin.com/in/example-maria-lopez',  'Met at the FIU career fair.'),
(2, 1, 'James Carter', 'Engineering Manager',      'james.carter@techcorp.example.com',  '305-555-0187', NULL,                                               'Hiring manager for Software Developer.'),
(3, 2, 'Priya Shah',   'Talent Acquisition Lead',  'priya.shah@dataco.example.com',      '512-555-0123', 'https://www.linkedin.com/in/example-priya-shah',   NULL),
(4, 3, 'Alex Nguyen',  'Senior DevOps Engineer',   'alex.nguyen@cloudnine.example.com',  NULL,           'https://www.linkedin.com/in/example-alex-nguyen',  'Referred me for the DevOps role.'),
(5, 4, 'Sarah Johnson','HR Coordinator',           'sarah.johnson@healthbridge.example.com', '407-555-0166', NULL,                                           NULL),
(6, 5, 'Daniel Kim',   'Quant Team Lead',          'daniel.kim@finedge.example.com',     '212-555-0199', 'https://www.linkedin.com/in/example-daniel-kim',   'Send thank-you note after offer call.');
