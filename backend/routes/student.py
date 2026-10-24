from flask import Blueprint, abort, render_template, request, session
from auth import role_required
from services import student as svc

bp = Blueprint('student', __name__)


@bp.route('/student')
@role_required('student')
def home():
    student_id = session.get('student_id')
    if not student_id:
        abort(403)
    student = svc.profile(student_id)
    if not student:
        abort(404)
    subjects = svc.subjects(student_id)
    subject = request.args.get('subject', '').strip()
    notice = None
    if subject and subject not in subjects:
        notice = ('error', 'Choose one of your subjects.')
        subject = ''
    summary = svc.summary(student_id, subject or None)
    rows = svc.history(student_id, subject or None)
    return render_template('student.html', student=student, subjects=subjects, subject=subject,
                           summary=summary, rows=rows, notice=notice)
