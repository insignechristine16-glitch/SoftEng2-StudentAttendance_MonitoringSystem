from db import get_db

PER_PAGE = 10

# Rate = (present + late) / (present + late + absent) x 100. Excused is excluded; NULL when nothing countable.
_SELECT = """
SELECT cs.id, cs.session_date, sec.code, sec.subject,
       COALESCE(SUM(a.status = 'present'), 0) AS present,
       COALESCE(SUM(a.status = 'late'), 0)    AS late,
       COALESCE(SUM(a.status = 'absent'), 0)  AS absent,
       COALESCE(SUM(a.status = 'excused'), 0) AS excused,
       CASE WHEN COALESCE(SUM(a.status IN ('present','late','absent')), 0) = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(a.status IN ('present','late'))
                       / SUM(a.status IN ('present','late','absent')), 1) END AS rate
FROM class_sessions cs
JOIN sections sec ON sec.id = cs.section_id
LEFT JOIN attendance a ON a.session_id = cs.id
"""


def _like(text):
    """Escape LIKE wildcards so a search for '%' or '_' is taken literally."""
    return '%' + text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


def _where(user_id, section_id, start, end, q):
    where, args = ['sec.instructor_id = ?'], [user_id]       # instructors only ever see their own sections
    if section_id:
        where.append('cs.section_id = ?'); args.append(section_id)
    if start:
        where.append('cs.session_date >= ?'); args.append(start.isoformat())
    if end:
        where.append('cs.session_date <= ?'); args.append(end.isoformat())
    if q:
        like = _like(q)
        where.append("""(sec.code LIKE ? ESCAPE '\\' OR sec.subject LIKE ? ESCAPE '\\' OR EXISTS (
                          SELECT 1 FROM attendance a2 JOIN students s ON s.id = a2.student_id
                          WHERE a2.session_id = cs.id
                            AND (s.name LIKE ? ESCAPE '\\' OR s.student_number LIKE ? ESCAPE '\\')))""")
        args += [like] * 4
    return ' AND '.join(where), args


def count_sessions(user_id, section_id=None, start=None, end=None, q=''):
    where, args = _where(user_id, section_id, start, end, q)
    return get_db().execute('SELECT COUNT(*) FROM class_sessions cs JOIN sections sec ON sec.id = cs.section_id '
                            f'WHERE {where}', args).fetchone()[0]


def list_sessions(user_id, section_id=None, start=None, end=None, q='', page=1):
    where, args = _where(user_id, section_id, start, end, q)
    return get_db().execute(
        f'{_SELECT} WHERE {where} GROUP BY cs.id ORDER BY cs.session_date DESC, sec.code LIMIT ? OFFSET ?',
        args + [PER_PAGE, (page - 1) * PER_PAGE]).fetchall()


def get_session(session_id, user_id):
    """The saved session with its section, only if the section belongs to this instructor."""
    return get_db().execute(
        'SELECT cs.id, cs.session_date, sec.id AS section_id, sec.code, sec.subject FROM class_sessions cs '
        'JOIN sections sec ON sec.id = cs.section_id WHERE cs.id = ? AND sec.instructor_id = ?',
        (session_id, user_id)).fetchone()


def apply_edit(session_id, user_id, changes, reason):
    """One transaction: every changed status and the edit_log row are saved together or not at all."""
    con = get_db()
    with con:
        con.executemany('UPDATE attendance SET status = ? WHERE session_id = ? AND student_id = ?',
                        [(status, session_id, student) for student, status in changes.items()])
        con.execute('INSERT INTO edit_log(session_id, user_id, reason) VALUES (?,?,?)',
                    (session_id, user_id, reason))