import sqlite3
from datetime import date
from flask import Blueprint, redirect, render_template, request, session, url_for
from auth import role_required
from services import attendance as svc
from services import dashboard as dash
from validators import parse_date, validate_marks

bp = Blueprint('instructor', __name__)


@bp.route('/instructor')
@role_required('instructor')
def dashboard():
    return render_template('dashboard.html', **dash.overview(session['user_id']))


@bp.route('/attendance', methods=['GET', 'POST'])
@role_required('instructor')
def take_attendance():
    uid = session['user_id']
    src = request.form if request.method == 'POST' else request.args
    section_id, day = src.get('section_id', type=int), src.get('date') or date.today().isoformat()
    ctx = dict(sections=svc.instructor_sections(uid), section_id=section_id, day=day, today=date.today().isoformat(),
               section=None, existing=None, rows=[], missing=set(), notice=None)

    section = svc.get_section(section_id, uid) if section_id else None
    d = parse_date(day)
    if section_id and not section:
        ctx['notice'] = ('error', 'Choose one of your assigned sections.')
    elif section and not d:
        ctx['notice'] = ('error', 'Enter a valid session date.')
    elif section:
        ctx['section'] = section
        existing = svc.find_session(section['id'], day)
        if existing:                                   # already saved: show it read-only
            ctx.update(existing=existing, rows=svc.session_rows(existing['id']))
            if request.method == 'POST':
                ctx['notice'] = ('error', 'Attendance for this section and date is already saved. Use Edit record to change it.')
            elif request.args.get('saved'):
                ctx['notice'] = ('success', f'Attendance saved successfully · {section["code"]} · {d:%B %d, %Y} · {len(ctx["rows"])} students')
        else:
            rows = svc.roster(section['id'])
            ctx['rows'] = rows
            if not rows:
                ctx['notice'] = ('warning', 'This section has no active students.')
            elif request.method == 'POST':
                marks, missing = validate_marks(request.form, [r['id'] for r in rows])
                for r in rows:                         # keep the instructor's selections
                    r['status'] = marks.get(r['id'])
                if d > date.today():
                    ctx['notice'] = ('error', 'Session date cannot be in the future.')
                elif missing:
                    n = len(missing)
                    ctx.update(missing=set(missing), notice=('warning',
                               f'{n} student{"s still need" if n > 1 else " still needs"} a status. '
                               'Mark every student before saving.'))
                else:
                    try:
                        svc.save_session(section['id'], day, uid, marks)
                    except sqlite3.IntegrityError:
                        ctx['notice'] = ('error', 'Could not save: a record for this section and date already exists.')
                    except sqlite3.Error:
                        ctx['notice'] = ('error', 'Could not save attendance because of a database error. Please try again.')
                    else:
                        return redirect(url_for('instructor.take_attendance', section_id=section['id'], date=day, saved=1))
    return render_template('attendance.html', **ctx)