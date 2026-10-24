import hmac
import secrets
from flask import abort, request, session

FIELD = 'csrf_token'
SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}


def token():
    """The signed-in visitor's CSRF token, created on first use.

    The token lives only in the Flask session, so a form posted from another site
    cannot know it.
    """
    if FIELD not in session:
        session[FIELD] = secrets.token_hex(32)
    return session[FIELD]


def init_app(app):
    @app.before_request
    def protect_from_csrf():
        if request.method in SAFE_METHODS:
            return
        sent = request.form.get(FIELD, '')
        expected = session.get(FIELD, '')
        if not expected or not hmac.compare_digest(sent, expected):
            abort(400, description='Your form session expired. Reload the page and try again.')

    app.context_processor(lambda: {'csrf_token': token})
