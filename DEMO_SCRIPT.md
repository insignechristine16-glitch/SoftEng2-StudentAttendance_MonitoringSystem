# Rollcall — demo script (about 6–8 minutes)

## Before the demo

```powershell
cd backend
..\venv\Scripts\python.exe seed.py
..\venv\Scripts\python.exe app.py
```

Open <http://127.0.0.1:5000> in a browser. Keep this terminal visible in case the instructor asks
about the server. Seed data is clean, so every number below will appear.

## 1. Administrator — students and sections (~2 minutes)

1. Sign in as `admin@school.edu` / `Admin@123`.
   - Point out that the admin lands on **Students**, not a placeholder.
   - Stats read **128 students shown**, **4 class sections**, **128 active enrollments**.
2. Search `Alex` and filter **BSIT 2A**. Show the matching row and the Active chip.
3. Click **Add student** and enter:
   - Student ID `2024-9001`, name `Isabel Santos`, email `isabel.santos@school.edu`, section `BSIT 2A`.
   - Submit. Point out the success notice and the new row.
4. Add a second student with the same ID but a different email.
   - Show the friendly message: “That student ID is already in use.” Cancel.
5. Edit Isabel, change **Enrollment status** to **Inactive**, save.
   - The chip changes to Inactive. Mention that this is the soft delete: history is kept and the
     student can no longer sign in.
6. Open **Class sections**. Point out the student count on each card. Open **Add section**, enter
   code `BSIT 4A`, then try the same code in lowercase — it is rejected. Cancel (or edit an existing
   section’s room and save).

What to say: “The admin manages the master data; validation and duplicate checks happen on the
server, not only in the browser.”

## 2. Instructor — attendance, records, reports (~3 minutes)

1. Sign out, then sign in as `instructor@school.edu` / `Instructor@123`.
   - The **Overview** shows 4 assigned classes, 128 enrolled students, an overall rate, sessions
     saved today, and a chart of the last 5 sessions.
2. Click **Take attendance**. Choose **BSIT 2A · Database Management**, date `2026-10-23`, and load
   the list.
3. Press **Save attendance** without marking anyone.
   - Show the warning that every student needs a status; nothing is saved.
4. Click **Mark remaining as present**, then save.
   - Show the success notice with the section, date, and student count.
5. Open **Attendance records**. The new 2026-10-23 session is at the top with counts and rate.
   - Instructors only see their own sections; this is enforced in SQL.
6. Open **Edit record** on that session. Change one student to **Absent**, type a reason, and save.
   - Show the success notice and the updated counts.
   - Try saving with no reason, or with no changed status, to show the validation messages.
7. Open **Reports**. Show the rate, sessions, student breakdown, status counts, and bar chart.
   - Filter by section or date range and generate again.

What to say: “A whole session is saved in one transaction; an edit saves the status changes and the
edit-log row together.”

## 3. Student — own attendance only (~1 minute)

1. Sign out, then sign in as `2024-0006` / `Student@123` (Hana Castro).
   - Show 8 sessions, 5 present, 1 late, 2 absent, rate **75.0%**.
2. Use the **Subject** filter, then clear it with **All subjects**.
3. In the address bar, add `?student_id=1` to `/student`.
   - It still shows Hana. Say: “The student ID comes from the signed-in session, never from the URL.”
4. Try `/students` while signed in as the student.
   - Show the custom **403 Access denied** page.

What to say: “Each student can only ever read their own rows.”

## 4. Error handling and security (~1 minute, optional)

- Visit `/does-not-exist` — custom **404** page with a link back to the dashboard.
- While signed in as student, visit `/instructor` — custom **403** page.
- Optional CSRF proof from PowerShell (server running, no session cookie):

  ```powershell
  Invoke-WebRequest -Method Post -Uri http://127.0.0.1:5000/ `
    -Body @{ role = 'student'; identifier = '2024-0018'; password = 'Student@123' }
  ```

  The response is the custom **400** page because the POST has no CSRF token. The browser forms all
  send the token, so normal use is unaffected.

Finish by signing out.

## Requirement checklist to mention

- Three working features: attendance marking, records/editing, reports, plus admin management and the
  student view.
- Appropriate UI: shared sidebar/topbar, cards, tables, charts, responsive CSS.
- Input validation: formats, required fields, dates, statuses, duplicate checks, ownership checks.
- Correct data handling: parameterized SQL, transactions, the agreed rate formula, soft delete.
- Error messages: friendly inline notices, incomplete-roster warnings, duplicate messages, custom
  error pages.
- Organized code: blueprints, services, validators, schema, and reusable templates.
