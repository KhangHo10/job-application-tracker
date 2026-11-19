# AI Usage

This document explains how I used AI tools during the development of this project, what I implemented myself, and what I learned.

## Overview

I developed this project using a combination of my own coding, problem-solving, and AI assistance. I used **Claude Code** as a coding assistant to help brainstorm ideas, generate initial implementations, debug issues, and improve code quality.

I was responsible for designing the database schema, deciding the application's features, defining the Job Match algorithm, and determining how the dashboard should work. I also worked directly with the codebase, reviewed and modified implementations, tested features, and made sure everything met the assignment requirements.

## Tools Used

I used **Claude Code** (Anthropic's AI coding assistant through VS Code, using a Claude Opus model).

| Area              | How I Worked with AI                                                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Database**      | Designed the schema, relationships, ENUM values, JSON structures, and constraints. Used AI to assist with SQL implementation and review. |
| **Frontend**      | Worked with Jinja templates, Bootstrap, CSS, and JavaScript. Used AI to help build and refine UI components and interactions.            |
| **Backend**       | Worked with Flask routes, SQL queries, form validation, and Job Match logic. Used AI to generate initial code and suggest improvements.  |
| **Testing**       | Tested features locally using MySQL and Flask. AI assisted with generating 52 pytest tests and identifying potential issues.             |
| **Debugging**     | Investigated errors, reviewed code, and used AI suggestions to help troubleshoot and fix bugs.                                           |
| **Documentation** | Used AI to assist with drafting and organizing project documentation.                                                                    |

## Development Process

I divided development into smaller milestones, starting with the database schema and progressing through CRUD functionality, dashboard features, Job Match, and testing.

Throughout development, I:

1. **Planned the architecture:** Defined database relationships, cascading deletes, JSON structures, transactions, and application functionality.
2. **Implemented and refined features:** Worked with the code directly while using Claude Code to assist with implementation and improvements.
3. **Tested functionality:** Ran the Flask application locally, tested CRUD operations, validated user inputs, and checked database behavior.
4. **Debugged issues:** Investigated unexpected behavior and adjusted implementations based on testing.
5. **Reviewed and committed changes:** Reviewed each milestone and managed Git commits myself.

## Examples of AI Prompts

Some prompts I used included:

- **"Please read my HANDOFF.md and start the implementation"** — Started implementation based on my project design.
- **"go"** — Continued to the next milestone after reviewing changes.
- **"Is the text in the HTML files supposed to be there?"** — Helped me understand Jinja template syntax.
- **"From this screen here, does it expose sensitive info?"** — Checked for sensitive information before recording the demo.

## Issues Encountered

AI-generated implementations were not always correct. Some problems I encountered included:

- **Database column names:** AI initially assumed certain column names that differed from previous assignment specifications.
- **Interview round validation:** Empty interview rows incorrectly triggered validation errors because the dropdown submitted a default value. The logic was adjusted to properly detect empty rows.
- **Dashboard rounding:** Python and Jinja rounded certain percentages inconsistently with the intended display. A custom percentage filter was implemented to ensure consistent rounding.

These issues reinforced the importance of reviewing, understanding, and testing AI-assisted code.

## My Contributions

My involvement extended beyond prompting AI. I actively participated in the development and verification of the application by:

- Designing the database schema, features, and application logic.
- Working directly with the frontend and backend code to review and refine functionality.
- Setting up MySQL Server 8.0, MySQL Workbench, and the local development environment.
- Testing application features, database operations, validation, and transactions.
- Reviewing and troubleshooting implementation issues.
- Modifying `.gitignore` and cleaning up `schema.sql` comments.
- Comparing the implementation against course assignments and requirements.
- Managing Git commits and recording the project demonstration.

## Lessons Learned

This project strengthened my understanding of **Flask, MySQL, database design, JSON data, transactions, frontend development, and testing**.

I also learned that AI is most effective when used as a supporting development tool rather than a replacement for programming knowledge. Although Claude Code helped accelerate implementation and debugging, I still needed to understand the code, evaluate its suggestions, identify problems, and verify that the application behaved correctly.

Overall, the project helped me gain practical experience building a full-stack application while learning how to incorporate AI assistance responsibly into my software development workflow.
