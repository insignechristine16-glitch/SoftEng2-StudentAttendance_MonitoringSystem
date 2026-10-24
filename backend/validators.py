#validators.py
import re
from datetime import datetime

ROLES = ('student', 'instructor', 'administrator')
STATUSES = ('present', 'late', 'absent', 'excused')
EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
STUDENT_ID = re.compile(r'\d{4}-\d{4}')


def validate_login(form):
    """Returns (clean_data, [error messages])."""
    role = form.get('role', '').strip()
    ident = form.get('identifier', '').strip()
    pw = form.get('password', '')
    errors = []
    if role not in ROLES:
        errors.append('Choose a valid role.')
    if not ident:
        errors.append('Enter your student ID or school email.')
    elif len(ident) > 120:
        errors.append('That ID or email is too long.')
    elif role == 'student' and '@' not in ident and not STUDENT_ID.fullmatch(ident):
        errors.append('Student ID must look like 2024-0018.')
    elif (role != 'student' or '@' in ident) and not EMAIL.fullmatch(ident):
        errors.append('Enter a valid school email address.')
    if not pw:
        errors.append('Enter your password.')
    return {'role': role, 'identifier': ident, 'password': pw}, errors


def parse_date(raw):
    """Strict YYYY-MM-DD -> date, or None if invalid."""
    try:
        return datetime.strptime(raw or '', '%Y-%m-%d').date()
    except ValueError:
        return None


def validate_marks(form, student_ids):
    """Returns ({student_id: status}, [student_ids still missing a valid status])."""
    marks = {i: form.get(f'status_{i}') for i in student_ids if form.get(f'status_{i}') in STATUSES}
    return marks, [i for i in student_ids if i not in marks]


REASON_MAX = 500

def validate_reason(form):
    """'Reason for change' on the edit screen. Returns (clean_reason, [error messages])."""
    reason = (form.get('reason') or '').strip()
    if not reason:
        return reason, ['Enter a reason for the change.']
    if len(reason) > REASON_MAX:
        return reason, [f'Reason must be {REASON_MAX} characters or fewer.']
    return reason, []

SECTION_FIELDS = {'code': ('Section code', 30), 'subject': ('Subject', 120), 'room': ('Room', 80), 'schedule': ('Schedule', 150)}

def validate_section(form, instructor_ids):
    """Returns (clean_data, [error messages]). Every problem is reported at once."""
    data = {k: ' '.join((form.get(k) or '').split()) for k in SECTION_FIELDS}      # trim + collapse spaces
    errors = []
    for key, (label, limit) in SECTION_FIELDS.items():
        if not data[key]:
            errors.append(f'{label} is required.')
        elif len(data[key]) > limit:
            errors.append(f'{label} must be {limit} characters or fewer.')
    data['instructor_id'] = form.get('instructor_id', type=int)
    if data['instructor_id'] not in instructor_ids:
        errors.append('Choose an assigned instructor from the list.')
    return data, errors


NAME_MAX = 100
EMAIL_MAX = 120

def validate_student(form, section_ids):
    """Create/edit student form. Returns (clean_data, [error messages]); uniqueness is checked by the service."""
    data = {
        'student_number': (form.get('student_number') or '').strip(),
        'name': ' '.join((form.get('name') or '').split()),
        'email': (form.get('email') or '').strip().lower(),
        'section_id': form.get('section_id', type=int),
        'active': 1 if form.get('active') == '1' else 0,
    }
    errors = []
    if not STUDENT_ID.fullmatch(data['student_number']):
        errors.append('Student ID must look like 2024-0018.')
    if not data['name']:
        errors.append('Full name is required.')
    elif len(data['name']) > NAME_MAX:
        errors.append(f'Full name must be {NAME_MAX} characters or fewer.')
    if not data['email']:
        errors.append('School email is required.')
    elif len(data['email']) > EMAIL_MAX or not EMAIL.fullmatch(data['email']):
        errors.append('Enter a valid school email address.')
    if data['section_id'] not in section_ids:
        errors.append('Choose a class section from the list.')
    return data, errors