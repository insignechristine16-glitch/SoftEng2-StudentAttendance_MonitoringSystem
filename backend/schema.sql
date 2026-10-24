PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id            INTEGER PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  name          TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('student','instructor','administrator'))
);

CREATE TABLE sections (
  id            INTEGER PRIMARY KEY,
  code          TEXT NOT NULL UNIQUE,
  subject       TEXT NOT NULL,
  room          TEXT NOT NULL,
  schedule      TEXT NOT NULL,
  instructor_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE students (
  id             INTEGER PRIMARY KEY,
  student_number TEXT NOT NULL UNIQUE,
  name           TEXT NOT NULL,
  section_id     INTEGER NOT NULL REFERENCES sections(id),
  active         INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),  -- soft delete
  user_id        INTEGER NOT NULL UNIQUE REFERENCES users(id)         -- email lives in users
);

CREATE TABLE class_sessions (
  id           INTEGER PRIMARY KEY,
  section_id   INTEGER NOT NULL REFERENCES sections(id),
  session_date TEXT NOT NULL,                                          -- YYYY-MM-DD
  created_by   INTEGER NOT NULL REFERENCES users(id),
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (section_id, session_date)                                    -- no duplicate sessions
);

CREATE TABLE attendance (
  id         INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES students(id),
  status     TEXT NOT NULL CHECK (status IN ('present','late','absent','excused')),
  UNIQUE (session_id, student_id)
);

CREATE TABLE edit_log (
  id         INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES class_sessions(id) ON DELETE CASCADE,
  user_id    INTEGER NOT NULL REFERENCES users(id),
  reason     TEXT NOT NULL,
  edited_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_section ON students(section_id);
CREATE INDEX idx_attendance_session ON attendance(session_id);
CREATE INDEX idx_attendance_student ON attendance(student_id);