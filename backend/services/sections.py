from db import get_db
from services.records import _like


def list_sections(q=''):
    """All sections with the instructor's name and the number of ACTIVE students; optional search."""
    where, args = '', []
    if q:
        like = _like(q)
        where = "WHERE sec.code LIKE ? ESCAPE '\\' OR sec.subject LIKE ? ESCAPE '\\' OR u.name LIKE ? ESCAPE '\\'"
        args = [like] * 3
    return get_db().execute(
        'SELECT sec.*, u.name AS instructor, '
        '(SELECT COUNT(*) FROM students s WHERE s.section_id = sec.id AND s.active = 1) AS students '
        f'FROM sections sec JOIN users u ON u.id = sec.instructor_id {where} ORDER BY sec.code', args).fetchall()


def get_section(section_id):
    return get_db().execute('SELECT * FROM sections WHERE id = ?', (section_id,)).fetchone()


def instructors():
    return get_db().execute("SELECT id, name FROM users WHERE role = 'instructor' ORDER BY name").fetchall()


def code_taken(code, exclude_id=None):
    """Case-insensitive duplicate check, so 'bsit 2a' and 'BSIT 2A' count as the same code."""
    return get_db().execute('SELECT 1 FROM sections WHERE code = ? COLLATE NOCASE AND id IS NOT ?',
                            (code, exclude_id)).fetchone() is not None


def save(data, section_id=None):
    """Insert (section_id None) or update one section. Returns its id."""
    con = get_db()
    fields = (data['code'], data['subject'], data['room'], data['schedule'], data['instructor_id'])
    with con:
        if section_id is None:
            return con.execute('INSERT INTO sections(code, subject, room, schedule, instructor_id) VALUES (?,?,?,?,?)',
                               fields).lastrowid
        con.execute('UPDATE sections SET code = ?, subject = ?, room = ?, schedule = ?, instructor_id = ? WHERE id = ?',
                    fields + (section_id,))
        return section_id