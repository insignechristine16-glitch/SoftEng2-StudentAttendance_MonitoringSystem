# Rollcall — Student Attendance Monitoring System

Software Engineering 2 · Laboratory Activity 6 · Task 3: Software Implementation

Team: Balagao, Insigne, Macalindong  
Submitted to: Gerald Jane Salacsacan · October 2026

Rollcall is a working web system for recording and reviewing class attendance. It has three roles
(student, instructor, administrator), a SQLite database, server-side validation, and a Jinja front end
based on the original HTML/CSS prototype.

## Requirements

- Python 3.10 or newer
- Flask 3 (`backend/requirements.txt`)

## Setup and run (Windows, VS Code)

The virtual environment is already in `venv/` at the project root.

```powershell
cd backend
..\venv\Scripts\python.exe -m pip install -r requirements.txt
..\venv\Scripts\python.exe seed.py      # creates rollcall.db with demo data
..\venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000>.

To start over with clean demo data, stop the server and run `python seed.py` again.

## Demo accounts

| Role          | Sign in                                                    | Password         |
| ------------- | ---------------------------------------------------------- | ---------------- |
| Administrator | `admin@school.edu`                                         | `Admin@123`      |
| Instructor    | `instructor@school.edu`                                    | `Instructor@123` |
| Student       | `2024-0018` (Alex Reyes) or `alex.reyes@student.rollcall.local` | `Student@123`    |

Every seeded student uses `Student@123`. A student created from the admin screen also starts with
`Student@123` (stored hashed).

Seed contents: 4 sections (BSIT 2A, 2B, 2C, 3A), 32 students each, 8 saved sessions per section
(2026-10-01 to 2026-10-22), and 1,024 attendance rows.

## What the system does

- **Sign in by role** with a student ID or school email and password. Inactive students cannot sign in.
- **Take attendance** for the instructor's own sections: choose section and date, load the roster,
  mark present/late/absent/excused, see live counts, search the roster, and save. Incomplete rosters
  and future dates are rejected with clear messages; a saved section/date cannot be saved twice.
- **Attendance records**: filter by section, date range, or search; paginate; open a record and edit
  statuses with a required reason. Every edit is written to `edit_log`.
- **Reports** for instructors and administrators: overall rate, session/student totals, a per-session
  bar chart, and a per-student breakdown. Excused marks are excluded from the rate.
- **Admin students**: search by name/ID, filter by section, add, edit, and soft delete by setting
  Enrollment status to Inactive. Creating a student also creates the linked user account.
- **Admin sections**: search, add, and edit sections; unique code and a valid instructor are required;
  each card shows the active student count.
- **Student self-view**: own rate, present/late/absent counts, and session history with an optional
  subject filter. The student is resolved from the login session, never from the URL.
- **Instructor overview**: assigned classes, enrolled students, overall rate, sessions saved today,
  and a chart of the last 5 sessions.

Rate = (Present + Late) ÷ (Present + Late + Absent) × 100. Excused is excluded; the rate shows “—” when
there is nothing countable.

## Validation, errors, and security

- Inputs are validated on the server (role, login identifier, student ID format `YYYY-NNNN`, names,
  email, section and instructor references, dates, statuses, required edit reasons, max lengths).
- Duplicate student IDs, emails, and section codes produce friendly messages.
- Passwords are hashed with Werkzeug.
- Writers only see and edit their own sections; role checks return a custom 403 page.
- Custom 400/403/404/500 pages replace Flask's default pages.
- CSRF tokens are required on every POST form, including sign-in.
- The sign-in and error pages use `frontend/asset/landing_bg.jpg` as a background.

## Project layout

```
backend/
  app.py, auth.py, csrf.py, db.py, schema.sql, seed.py, validators.py
  requirements.txt, rollcall.db (created by seed.py)
  routes/       auth (in auth.py), instructor, records, reports, admin, student
  services/     attendance, records, reports, students, sections, student, dashboard
frontend/
  asset/        styles.css, landing_bg.jpg
  templates/    base, index (sign-in), error, attendance, edit-record, records,
                dashboard, reports, students, student-form, sections, section-form, student
```

## Notes

- The dev server uses `debug=True` for the demo; set a real `SECRET_KEY` environment variable for
  anything beyond the classroom demo. With `debug=True`, Flask shows its debugger for unexpected
  exceptions; the custom 500 page is used when debug is off.
- The unused prototype files from Task 2C are kept under `frontend/templates/` for reference
  (`design-notes.html`, `attendance-*.html`, `login-error.html`, `record-updated.html`,
  `admin-reports.html`). They are not served by the application.
