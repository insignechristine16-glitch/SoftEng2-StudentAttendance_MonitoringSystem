#app.py
#app.py
import os
from pathlib import Path
from flask import Flask, render_template, session, url_for
import auth, csrf, db
from routes import admin, instructor, records, reports, student

BACKEND = Path(__file__).resolve().parent
FRONTEND = BACKEND.parent / 'frontend'

ERROR_TITLES = {400: 'Request could not be completed', 403: 'Access denied',
                404: 'Page not found', 500: 'Something went wrong'}
ERROR_MESSAGES = {
    403: 'You do not have permission to open this page with your account.',
    404: 'The page you are looking for does not exist or may have been moved.',
    500: 'The server ran into a problem. Please try again in a moment.',
}


def _error_page(error):
    code = getattr(error, 'code', 500) or 500
    role = session.get('role')
    signed_in = role in auth.HOME
    home = url_for(auth.HOME[role]) if signed_in else url_for('auth.login')
    message = error.description if code == 400 and error.description else ERROR_MESSAGES.get(code, ERROR_MESSAGES[500])
    return render_template('error.html', code=code, title=ERROR_TITLES.get(code, ERROR_TITLES[500]),
                           message=message, home=home, signed_in=signed_in), code


def create_app():
    app = Flask(__name__, template_folder=FRONTEND / 'templates',
                static_folder=FRONTEND / 'asset', static_url_path='/asset')
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-only-change-me'),
                      DATABASE=str(BACKEND / 'rollcall.db'))
    db.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(instructor.bp)
    app.register_blueprint(records.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(student.bp)
    for code in (400, 403, 404, 500):
        app.register_error_handler(code, _error_page)
    return app


if __name__ == '__main__':
    create_app().run(debug=True)