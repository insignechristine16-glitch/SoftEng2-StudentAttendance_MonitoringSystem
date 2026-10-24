import sqlite3
from flask import Blueprint, abort, redirect, render_template, request, url_for
from auth import role_required
from services import sections as sec_svc
from services import students as stu_svc
from validators import validate_section, validate_student

bp = Blueprint('admin', __name__)


def _duplicate_errors(data, student=None):
    """Friendly duplicate messages. student is the existing row when editing."""
    errors = []
    if stu_svc.number_taken(data['student_number'], student['id'] if student else None):
        errors.append('That student ID is already in use.')
    if stu_svc.email_taken(data['email'], student['user_id'] if student else None):
        errors.append('That school email is already registered.')
    return errors


def _save_error(action):
    return f'Could not {action} because of a database error. Please try again.'


# ---------------------------------------------------------------- students

@bp.route('/students')
@role_required('administrator')
def students():
    q = request.args.get('q', '').strip()[:80]
    section_id = request.args.get('section_id', type=int)
    sections = sec_svc.list_sections()

    notice = None
    bad_section = bool(section_id) and section_id not in {s['id'] for s in sections}
    if bad_section:
        notice = ('error', 'Choose one of the listed sections.')
    elif request.args.get('saved'):
        notice = ('success', 'Student record saved successfully.')

    rows = stu_svc.list_students(q, None if bad_section else section_id)
    stats = {'shown': len(rows), 'sections': len(sections), 'active': sum(r['active'] for r in rows)}
    return render_template('students.html', rows=rows, sections=sections, q=q, section_id=section_id,
                           stats=stats, notice=notice)


@bp.route('/students/add', methods=['GET', 'POST'])
@role_required('administrator')
def add_student():
    sections = sec_svc.list_sections()
    data = {'student_number': '', 'name': '', 'email': '', 'section_id': None, 'active': 1}
    errors = []
    if request.method == 'POST':
        data, errors = validate_student(request.form, {s['id'] for s in sections})
        errors += _duplicate_errors(data)
        if not errors:
            try:
                stu_svc.save(data)
            except sqlite3.IntegrityError:
                errors.append('That student ID or school email is already in use.')
            except sqlite3.Error:
                errors.append(_save_error('save the student'))
            else:
                return redirect(url_for('admin.students', saved=1))
    return render_template('student-form.html', student=None, data=data, errors=errors, sections=sections)


@bp.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
@role_required('administrator')
def edit_student(student_id):
    student = stu_svc.get_student(student_id) or abort(404)
    sections = sec_svc.list_sections()
    data, errors = dict(student), []
    if request.method == 'POST':
        data, errors = validate_student(request.form, {s['id'] for s in sections})
        errors += _duplicate_errors(data, student)
        if not errors:
            try:
                stu_svc.save(data, student_id)
            except sqlite3.IntegrityError:
                errors.append('That student ID or school email is already in use.')
            except sqlite3.Error:
                errors.append(_save_error('save the student'))
            else:
                return redirect(url_for('admin.students', saved=1))
    return render_template('student-form.html', student=student, data=data, errors=errors, sections=sections)


# ---------------------------------------------------------------- sections

@bp.route('/sections')
@role_required('administrator')
def sections():
    q = request.args.get('q', '').strip()[:80]
    notice = ('success', 'Section saved successfully.') if request.args.get('saved') else None
    return render_template('sections.html', rows=sec_svc.list_sections(q), q=q, notice=notice)


@bp.route('/sections/add', methods=['GET', 'POST'])
@role_required('administrator')
def add_section():
    instructors = sec_svc.instructors()
    data = {'code': '', 'subject': '', 'room': '', 'schedule': '', 'instructor_id': None}
    errors = []
    if request.method == 'POST':
        data, errors = validate_section(request.form, {i['id'] for i in instructors})
        if not errors and sec_svc.code_taken(data['code']):
            errors.append('That section code is already in use.')
        if not errors:
            try:
                sec_svc.save(data)
            except sqlite3.IntegrityError:
                errors.append('That section code is already in use.')
            except sqlite3.Error:
                errors.append(_save_error('save the section'))
            else:
                return redirect(url_for('admin.sections', saved=1))
    return render_template('section-form.html', section=None, data=data, errors=errors, instructors=instructors)


@bp.route('/sections/<int:section_id>/edit', methods=['GET', 'POST'])
@role_required('administrator')
def edit_section(section_id):
    section = sec_svc.get_section(section_id) or abort(404)
    instructors = sec_svc.instructors()
    data, errors = dict(section), []
    if request.method == 'POST':
        data, errors = validate_section(request.form, {i['id'] for i in instructors})
        if not errors and sec_svc.code_taken(data['code'], section_id):
            errors.append('That section code is already in use.')
        if not errors:
            try:
                sec_svc.save(data, section_id)
            except sqlite3.IntegrityError:
                errors.append('That section code is already in use.')
            except sqlite3.Error:
                errors.append(_save_error('save the section'))
            else:
                return redirect(url_for('admin.sections', saved=1))
    return render_template('section-form.html', section=section, data=data, errors=errors, instructors=instructors)
