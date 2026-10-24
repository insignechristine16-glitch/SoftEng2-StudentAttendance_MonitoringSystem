from db import get_db

CHART_SESSIONS = 10      # the bar chart shows the most recent sessions only


def rate(present, late, absent):
    """(Present + Late) / (Present + Late + Absent) x 100. Excused is excluded. None if nothing countable."""
    counted = present + late + absent
    return round(100 * (present + late) / counted, 1) if counted else None


def report_sections(user_id=None):
    """Sections a report may cover: the instructor's own, or every section when user_id is None (admin)."""
    sql, args = 'SELECT * FROM sections', []
    if user_id is not None:
        sql, args = sql + ' WHERE instructor_id = ?', [user_id]
    return get_db().execute(sql + ' ORDER BY code', args).fetchall()


def _where(user_id, section_id, start, end):
    where, args = ['1 = 1'], []
    if user_id is not None:                      # instructors only ever see their own sections
        where.append('sec.instructor_id = ?'); args.append(user_id)
    if section_id:
        where.append('cs.section_id = ?'); args.append(section_id)
    if start:
        where.append('cs.session_date >= ?'); args.append(start.isoformat())
    if end:
        where.append('cs.session_date <= ?'); args.append(end.isoformat())
    return ' AND '.join(where), args


_COUNTS = """COALESCE(SUM(a.status = 'present'), 0) AS present, COALESCE(SUM(a.status = 'late'), 0) AS late,
             COALESCE(SUM(a.status = 'absent'), 0) AS absent, COALESCE(SUM(a.status = 'excused'), 0) AS excused"""
_FROM = """FROM class_sessions cs JOIN sections sec ON sec.id = cs.section_id
           LEFT JOIN attendance a ON a.session_id = cs.id"""


def build_report(user_id=None, section_id=None, start=None, end=None):
    """One report for both roles. Returns totals, per-session rows (chart) and per-student rows (table)."""
    con = get_db()
    where, args = _where(user_id, section_id, start, end)

    t = con.execute(f"SELECT COUNT(DISTINCT cs.id) AS sessions, COUNT(DISTINCT a.student_id) AS students, {_COUNTS} "
                    f"{_FROM} WHERE {where}", args).fetchone()
    totals = dict(t, rate=rate(t['present'], t['late'], t['absent']))

    sessions = [dict(r, rate=rate(r['present'], r['late'], r['absent'])) for r in con.execute(
        f"SELECT cs.id, cs.session_date, sec.code, {_COUNTS} {_FROM} WHERE {where} "
        'GROUP BY cs.id ORDER BY cs.session_date DESC, sec.code DESC LIMIT ?', args + [CHART_SESSIONS])][::-1]

    students = [dict(r, rate=rate(r['present'], r['late'], r['absent'])) for r in con.execute(
        f"SELECT s.id, s.student_number, s.name, s.active, sec.code, {_COUNTS} {_FROM} "
        f"JOIN students s ON s.id = a.student_id WHERE {where} GROUP BY s.id ORDER BY s.name", args)]
    students.sort(key=lambda r: (r['rate'] is None, r['rate'] if r['rate'] is not None else 0))  # lowest rate first
    return {'totals': totals, 'sessions': sessions, 'students': students}