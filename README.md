# Job Application Tracker

A full-stack web application I developed for my **COP4751 – Advanced Database Management** course project. The application helps users organize their job search by managing companies, job postings, applications, interview rounds, and professional contacts.

It also includes a **Job Match** feature that compares users' skills against job requirements and ranks opportunities based on compatibility.

**Tech Stack:** Python, Flask, MySQL 8, HTML, CSS, JavaScript, Bootstrap 5, and Jinja2.

## Features

- **CRUD Operations:** Create, view, update, and delete companies, jobs, applications, and contacts.
- **Search & Filtering:** Search companies and filter jobs, applications, and contacts by different criteria.
- **Dashboard:** View application statistics, response rates, recent applications, and upcoming interviews.
- **Job Match:** Compare entered skills against job requirements, calculate match percentages, and identify missing skills.
- **Interview Tracking:** Add multiple interview rounds with dates, types, interviewers, and notes, stored using MySQL JSON columns.
- **Form Validation:** Client-side and server-side validation for required fields, formats, salary ranges, and ENUM values.
- **Database Transactions:** Create an application and an optional contact in a single transaction with rollback support.
- **Safe Deletion:** Display confirmation messages and affected records before cascading deletes.


## Demo Video

A walkthrough of the application's main features.

https://github.com/user-attachments/assets/bfa17416-4b86-424e-8f2c-eaf520679804

## Getting Started

### Requirements

- Python 3.10+
- MySQL Server 8.0.16+
- MySQL Workbench (optional)

### 1. Clone and Install

```bash
git clone <repository-url>
cd job-application-tracker

python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Set Up the Database

Run `schema.sql` using MySQL Workbench or the command line:

```bash
mysql -u root -p < schema.sql
```

This creates the `job_tracker` database, including the tables, relationships, indexes, and sample data.

**Note:** The script uses `DROP DATABASE IF EXISTS job_tracker`, so running it again will reset the database.

### 3. Configure Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Update the database credentials and Flask secret key:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=job_tracker
DB_USER=root
DB_PASSWORD=your_password
FLASK_SECRET_KEY=your_secret_key
```

The `.env` file is excluded from Git to protect sensitive credentials.

### 4. Run the Application

```bash
python app.py
```

Open [**http://127.0.0.1:5000**](http://127.0.0.1:5000) in your browser.

### 5. Run Tests

```bash
python -m pytest
```

The project includes 52 pytest tests covering validation, Job Match calculations, and Flask routes. Unit tests do not require MySQL, while route tests use the local database when available.

## Database Design

The application uses four relational tables:

```text
companies
   ├── jobs
   │     └── applications
   └── contacts
```

| Table          | Description                                                            |
| -------------- | ---------------------------------------------------------------------- |
| `companies`    | Stores company information                                             |
| `jobs`         | Stores job postings, salaries, requirements, and company relationships |
| `applications` | Tracks applications, statuses, and interview rounds                    |
| `contacts`     | Stores professional contacts associated with companies                 |

### Key Database Concepts

- **Foreign Keys:** Enforce relationships using `ON DELETE CASCADE`.
- **JSON Data Types:** Store job requirements and interview information in flexible structures.
- **JSON_TABLE:** Extract interview rounds from JSON for dashboard queries.
- **Indexes:** Improve performance for job searches, company filters, and application statuses.
- **CHECK Constraints:** Prevent invalid data, such as salary minimums exceeding maximums.
- **Transactions:** Ensure related application and contact records are saved together or rolled back.
- **Parameterized Queries:** Protect SQL operations against SQL injection.

## Job Match Algorithm

The Job Match feature compares a user's skills against the required skills stored in each job's JSON data.

The match percentage is calculated as:

```text
Match % = (Matched Skills / Required Skills) × 100
```

For example, a user entering `Python, SQL, Flask` would receive a 100% match for a job requiring all three skills.

The results display matching skills, missing skills, and a progress bar, allowing users to quickly identify opportunities that align with their experience.

## Project Structure

```text
job-application-tracker/
├── app.py              # Flask routes and application logic
├── database.py         # Database queries and transactions
├── validators.py       # Server-side form validation
├── matching.py         # Job Match algorithm
├── schema.sql          # Database schema and sample data
├── templates/          # Jinja2 HTML templates
├── static/
│   ├── style.css       # Custom styling
│   └── app.js          # Frontend interactions
├── media/
|   ├── Demo_Video.mp4      # Custom styling
├── tests/              # Pytest test suite
├── requirements.txt    # Python dependencies
├── .env.example        # Environment configuration template
├── AI_USAGE.md         # AI assistance documentation
└── README.md
```

## Development & Learning

Through this project, I gained practical experience designing and implementing a relational database within a full-stack web application.

I worked with MySQL features such as JSON columns, foreign keys, indexing, constraints, and transactions, while integrating them with a Flask backend and an interactive frontend.

I also practiced debugging, testing, and organizing application code into maintainable components.

AI tools were used to support parts of the development process, including brainstorming, implementation assistance, debugging, and documentation. My specific contributions and AI usage are documented in [AI_USAGE.md](AI_USAGE.md).

---

**Course:** COP4751 – Advanced Database Management
**Project:** Job Application Tracker
