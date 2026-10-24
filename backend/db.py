import sqlite3
from pathlib import Path
from flask import current_app, g

SCHEMA = Path(__file__).with_name('schema.sql')


def connect(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def get_db():
    if 'db' not in g:
        g.db = connect(current_app.config['DATABASE'])
    return g.db


def close_db(_=None):
    con = g.pop('db', None)
    if con:
        con.close()


def init_app(app):
    app.teardown_appcontext(close_db)


def init_schema(path):
    """Create a fresh database file from schema.sql (used by seed.py)."""
    con = connect(path)
    con.executescript(SCHEMA.read_text())
    return con