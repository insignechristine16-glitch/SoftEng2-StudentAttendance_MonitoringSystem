from db import get_db


def instructor_sections(user_id):
    return get_db().execute('SELECT * FROM sections WHERE instructor_id = ? ORDER BY code', (user_id,)).fetchall()


def get_section(section_id, user_id):
    """Only returns the section if it belongs to this instructor."""
    return get_db().execute('SELECT * FROM sections WHERE id = ? AND instructor_id = ?',
                            (section_id, user_id)).fetchone()


def roster(section_id):
    """Active students of a section, each with an empty status."""
    rows = get_db().execute('SELECT id, student_number, name FROM students WHERE section_id = ? AND active = 1 '
                            'ORDER BY name', (section_id,))
    return [dict(r, status=None) for r in rows]


def find_session(section_id, day):
    return get_db().execute('SELECT * FROM class_sessions WHERE section_id = ? AND session_date = ?',
                            (section_id, day)).fetchone()


def session_rows(session_id):
    """Saved marks for a session (includes students deactivated since)."""
    rows = get_db().execute('SELECT s.id, s.student_number, s.name, a.status FROM attendance a '
                            'JOIN students s ON s.id = a.student_id WHERE a.session_id = ? ORDER BY s.name',
                            (session_id,))
    return [dict(r) for r in rows]


def save_session(section_id, day, user_id, marks):
    """One transaction: the session row and every attendance row are saved together or not at all."""
    con = get_db()
    with con:
        sid = con.execute('INSERT INTO class_sessions(section_id, session_date, created_by) VALUES (?,?,?)',
                          (section_id, day, user_id)).lastrowid
        con.executemany('INSERT INTO attendance(session_id, student_id, status) VALUES (?,?,?)',
                        [(sid, student, status) for student, status in marks.items()])
    return sid