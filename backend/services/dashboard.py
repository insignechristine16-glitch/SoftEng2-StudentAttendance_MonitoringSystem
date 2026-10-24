from datetime import date
from db import get_db
from services.reports import rate

RECENT_SESSIONS = 5


def classes(user_id):
    """The instructor's sections with their number of active students."""
    return get_db().execute(
        'SELECT sec.*, (SELECT COUNT(*) FROM students s WHERE s.section_id = sec.id AND s.active = 1) AS students '
        'FROM sections sec WHERE sec.instructor_id = ? ORDER BY sec.code', (user_id,)).fetchall()


def overview(user_id):
    con = get_db()
    enrolled = con.execute(
        'SELECT COUNT(*) FROM students s JOIN sections sec ON sec.id = s.section_id '
        'WHERE sec.instructor_id = ? AND s.active = 1', (user_id,)).fetchone()[0]
    totals = con.execute(
        "SELECT COALESCE(SUM(a.status = 'present'), 0) AS present, COALESCE(SUM(a.status = 'late'), 0) AS late, "
        "COALESCE(SUM(a.status = 'absent'), 0) AS absent, COALESCE(SUM(a.status = 'excused'), 0) AS excused "
        "FROM class_sessions cs JOIN sections sec ON sec.id = cs.section_id "
        "LEFT JOIN attendance a ON a.session_id = cs.id WHERE sec.instructor_id = ?", (user_id,)).fetchone()
    saved_today = con.execute(
        "SELECT COUNT(*) FROM class_sessions cs JOIN sections sec ON sec.id = cs.section_id "
        "WHERE sec.instructor_id = ? AND DATE(cs.created_at) = DATE('now', 'localtime')", (user_id,)).fetchone()[0]

    recent = [dict(r, rate=rate(r['present'], r['late'], r['absent'])) for r in con.execute(
        "SELECT cs.id, cs.session_date, sec.code, sec.subject, "
        "COALESCE(SUM(a.status = 'present'), 0) AS present, COALESCE(SUM(a.status = 'late'), 0) AS late, "
        "COALESCE(SUM(a.status = 'absent'), 0) AS absent, COALESCE(SUM(a.status = 'excused'), 0) AS excused "
        "FROM class_sessions cs JOIN sections sec ON sec.id = cs.section_id "
        "LEFT JOIN attendance a ON a.session_id = cs.id WHERE sec.instructor_id = ? "
        "GROUP BY cs.id ORDER BY cs.session_date DESC, cs.id DESC LIMIT ?", (user_id, RECENT_SESSIONS))][::-1]

    return {'classes': classes(user_id), 'enrolled': enrolled, 'saved_today': saved_today, 'today': date.today(),
            'rate': rate(totals['present'], totals['late'], totals['absent']), 'recent': recent}
