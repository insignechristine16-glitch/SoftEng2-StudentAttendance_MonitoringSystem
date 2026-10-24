from flask import Blueprint, render_template, request, session
from auth import role_required
from services import reports as svc
from validators import parse_date

bp = Blueprint('reports', __name__)


def _show(user_id, admin):
    """Shared by both roles. user_id=None means 'all sections' (administrator)."""
    sections = svc.report_sections(user_id)
    section_id = request.args.get('section_id', type=int)
    start_raw, end_raw = request.args.get('start_date', '').strip(), request.args.get('end_date', '').strip()
    start, end = parse_date(start_raw), parse_date(end_raw)

    notice = None
    if section_id and section_id not in {s['id'] for s in sections}:
        notice = ('error', 'Choose one of the listed sections.')
    elif start_raw and not start:
        notice = ('error', 'Enter a valid From date.')
    elif end_raw and not end:
        notice = ('error', 'Enter a valid To date.')
    elif start and end and start > end:
        notice = ('error', 'The From date must be on or before the To date.')

    report = None if notice else svc.build_report(user_id, section_id, start, end)
    return render_template('reports.html', admin=admin, sections=sections, section_id=section_id,
                           start=start_raw, end=end_raw, notice=notice, report=report,
                           action=request.path)


@bp.route('/reports')
@role_required('instructor')
def instructor():
    return _show(session['user_id'], admin=False)


@bp.route('/admin/reports')
@role_required('administrator')
def admin():
    return _show(None, admin=True)

