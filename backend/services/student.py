from db import get_db
from services.reports import rate


def profile(student_id):
    return get_db().execute(
        'SELECT s.id, s.student_number, s.name, s.active, sec.id AS section_id, sec.code, sec.subject '
        'FROM students s JOIN sections sec ON sec.id = s.section_id WHERE s.id = ?', (student_id,)).fetchone()


def subjects(student_id):
    """Distinct subjects this student has attendance for (used by the optional filter)."""
    return [r['subject'] for r in get_db().execute(
        'SELECT DISTINCT sec.subject FROM attendance a '
        'JOIN class_sessions cs ON cs.id = a.session_id JOIN sections sec ON sec.id = cs.section_id '
        'WHERE a.student_id = ? ORDER BY sec.subject', (student_id,))]


def _where(student_id, subject):
    where, args = ['a.student_id = ?'], [student_id]
    if subject:
        where.append('sec.subject = ?'); args.append(subject)
    return ' AND '.join(where), args


def summary(student_id, subject=None):
    where, args = _where(student_id, subject)
    row = get_db().execute(
        "SELECT COUNT(*) AS sessions, COALESCE(SUM(a.status = 'present'), 0) AS present, "
        "COALESCE(SUM(a.status = 'late'), 0) AS late, COALESCE(SUM(a.status = 'absent'), 0) AS absent, "
        "COALESCE(SUM(a.status = 'excused'), 0) AS excused "
        "FROM attendance a JOIN class_sessions cs ON cs.id = a.session_id "
        f"JOIN sections sec ON sec.id = cs.section_id WHERE {where}", args).fetchone()
    return dict(row, rate=rate(row['present'], row['late'], row['absent']))


def history(student_id, subject=None):
    where, args = _where(student_id, subject)
    return get_db().execute(
        'SELECT cs.session_date, sec.subject, sec.code, a.status FROM attendance a '
        'JOIN class_sessions cs ON cs.id = a.session_id JOIN sections sec ON sec.id = cs.section_id '
        f'WHERE {where} ORDER BY cs.session_date DESC, sec.code', args).fetchall()
