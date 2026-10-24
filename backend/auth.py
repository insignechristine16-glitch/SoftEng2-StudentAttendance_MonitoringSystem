from functools import wraps
from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from db import get_db
from validators import ROLES, validate_login

bp = Blueprint('auth', __name__)
HOME = {'student': 'student.home', 'instructor': 'instructor.dashboard', 'administrator': 'admin.students'}

def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*a, **k)
    return wrapper

def role_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **k):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session['role'] not in roles:
                abort(403)
            return f(*a, **k)
        return wrapper
    return deco

def find_user(role, ident):
    """Students sign in with student ID or email; staff with email. Inactive students are blocked."""
    return get_db().execute(
        """SELECT u.*, s.id AS student_id FROM users u
           LEFT JOIN students s ON s.user_id = u.id
           WHERE u.role = ? AND (u.email = ? OR s.student_number = ?)
             AND COALESCE(s.active, 1) = 1""", (role, ident, ident)).fetchone()

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and 'role' in session:
        return redirect(url_for(HOME[session['role']]))
    role, ident, error = 'student', '', None
    if request.method == 'POST':
        data, errors = validate_login(request.form)
        role = data['role'] if data['role'] in ROLES else 'student'
        ident = data['identifier']
        if errors:
            error = errors[0]
        else:
            user = find_user(role, ident)
            if user and check_password_hash(user['password_hash'], data['password']):
                session.clear()
                session.update(user_id=user['id'], role=user['role'], name=user['name'],
                               student_id=user['student_id'])
                return redirect(url_for(HOME[role]))
            error = 'Check your ID or email and password, then try again.'
    return render_template('index.html', role=role, ident=ident, error=error)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))