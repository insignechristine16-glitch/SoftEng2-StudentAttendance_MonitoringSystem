from werkzeug.security import generate_password_hash
from db import get_db
from services.records import _like

DEFAULT_PASSWORD = 'Student@123'

_SELECT = """SELECT s.id, s.student_number, s.name, s.section_id, s.active, s.user_id,
                    u.email, sec.code AS section_code
             FROM students s
             JOIN users u ON u.id = s.user_id
             JOIN sections sec ON sec.id = s.section_id"""


def list_students(q='', section_id=None):
    """All students matching an optional name/ID search and section filter, ordered by name."""
    where, args = ['1 = 1'], []
    if q:
        like = _like(q)
        where.append("(s.name LIKE ? ESCAPE '\\' OR s.student_number LIKE ? ESCAPE '\\')")
        args += [like, like]
    if section_id:
        where.append('s.section_id = ?'); args.append(section_id)
    return get_db().execute(f'{_SELECT} WHERE {" AND ".join(where)} ORDER BY s.name', args).fetchall()


def get_student(student_id):
    return get_db().execute(f'{_SELECT} WHERE s.id = ?', (student_id,)).fetchone()


def number_taken(student_number, exclude_id=None):
    return get_db().execute('SELECT 1 FROM students WHERE student_number = ? AND id IS NOT ?',
                            (student_number, exclude_id)).fetchone() is not None


def email_taken(email, exclude_user_id=None):
    """Case-insensitive, because users.email is COLLATE NOCASE."""
    return get_db().execute('SELECT 1 FROM users WHERE email = ? COLLATE NOCASE AND id IS NOT ?',
                            (email, exclude_user_id)).fetchone() is not None


def save(data, student_id=None):
    """Insert (student_id None) or update one student. Creates the linked users row on insert.

    The user row and student row are written in one transaction, so a failure leaves neither behind.
    """
    con = get_db()
    with con:
        if student_id is None:
            user_id = con.execute(
                'INSERT INTO users(email, password_hash, name, role) VALUES (?,?,?,?)',
                (data['email'], generate_password_hash(DEFAULT_PASSWORD), data['name'], 'student')).lastrowid
            return con.execute(
                'INSERT INTO students(student_number, name, section_id, active, user_id) VALUES (?,?,?,?,?)',
                (data['student_number'], data['name'], data['section_id'], data['active'], user_id)).lastrowid
        con.execute(
            'UPDATE users SET email = ?, name = ? WHERE id = (SELECT user_id FROM students WHERE id = ?)',
            (data['email'], data['name'], student_id))
        con.execute('UPDATE students SET student_number = ?, name = ?, section_id = ?, active = ? WHERE id = ?',
                    (data['student_number'], data['name'], data['section_id'], data['active'], student_id))
        return student_id
