import sqlite3
from math import ceil
from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from auth import role_required
from services import attendance as att
from services import records as svc
from validators import parse_date, validate_marks, validate_reason

bp = Blueprint('records', __name__)


@bp.route('/records')
@role_required('instructor')
def index():
    uid = session['user_id']
    section_id = request.args.get('section_id', type=int)
    start_raw = request.args.get('start_date', '').strip()
    end_raw = request.args.get('end_date', '').strip()
    q = request.args.get('q', '').strip()[:80]
    start, end = parse_date(start_raw), parse_date(end_raw)
    sections = att.instructor_sections(uid)

    notice = None
    if request.args.get('updated'):
        notice = ('success', 'Attendance changes saved successfully.')
    if section_id and not att.get_section(section_id, uid):
        notice = ('error', 'Choose one of your assigned sections.')
    elif start_raw and not start:
        notice = ('error', 'Enter a valid From date.')
    elif end_raw and not end:
        notice = ('error', 'Enter a valid To date.')
    elif start and end and start > end:
        notice = ('error', 'The From date must be on or before the To date.')

    rows, total, page = [], 0, 1
    if not (notice and notice[0] == 'error'):
        total = svc.count_sessions(uid, section_id, start, end, q)
        page = min(max(request.args.get('page', 1, type=int), 1), max(ceil(total / svc.PER_PAGE), 1))
        rows = svc.list_sessions(uid, section_id, start, end, q, page)

    filters = {k: v for k, v in (('section_id', section_id), ('start_date', start_raw),
                                 ('end_date', end_raw), ('q', q)) if v}
    return render_template('records.html', sections=sections, rows=rows, total=total, page=page,
                           pages=max(ceil(total / svc.PER_PAGE), 1), per_page=svc.PER_PAGE, filters=filters,
                           section_id=section_id, start=start_raw, end=end_raw, q=q, notice=notice)


@bp.route('/records/<int:session_id>/edit', methods=['GET', 'POST'])
@role_required('instructor')
def edit(session_id):
    uid = session['user_id']
    rec = svc.get_session(session_id, uid)
    if not rec:
        abort(404)                      # not found, or not this instructor's section
    rows = att.session_rows(session_id)
    original = {r['id']: r['status'] for r in rows}
    reason, notice, missing = '', None, set()

    if request.method == 'POST':
        marks, missing_ids = validate_marks(request.form, list(original))
        reason, errors = validate_reason(request.form)
        for r in rows:                  # keep the instructor's selections when the form re-renders
            r['status'] = marks.get(r['id'])
        if missing_ids:
            n = len(missing_ids)
            missing = set(missing_ids)
            notice = ('warning', f'{n} student{"s still need" if n > 1 else " still needs"} a status. '
                                 'Mark every student before saving.')
        elif errors:
            notice = ('error', errors[0])
        else:
            changes = {i: s for i, s in marks.items() if s != original[i]}
            if not changes:
                notice = ('warning', 'No statuses were changed. Change at least one status before saving.')
            else:
                try:
                    svc.apply_edit(session_id, uid, changes, reason)
                except sqlite3.Error:
                    notice = ('error', 'Could not save the changes because of a database error. Please try again.')
                else:
                    return redirect(url_for('records.index', updated=1))
    return render_template('edit-record.html', rec=rec, rows=rows, missing=missing, reason=reason, notice=notice)