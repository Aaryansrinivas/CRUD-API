import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

# Loaded from .env by python-dotenv in main.py before this module is used.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://taskuser:taskpass@localhost:5432/taskdb",
)


@contextmanager
def get_connection():
    """Open one connection, hand it out, always close it — even on error.
    A context manager is the Python idiom for 'always clean up after yourself',
    the same idea as 'finally' blocks or try-with-resources in other languages."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
