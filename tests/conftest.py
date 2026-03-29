import pytest
import sys
import os
import tempfile

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Create temp test database BEFORE any app imports
TEST_DB = tempfile.mktemp(suffix='.db')

# Patch Config.DATABASE_PATH before anything else imports it
import config
config.Config.DATABASE_PATH = TEST_DB

# Also patch os.environ so get_db() in database.py uses TEST_DB at runtime
os.environ['DATABASE_PATH'] = TEST_DB
os.environ['TESTING'] = '1'

# Force-create tables in TEST_DB right now, before any test code runs
# This guarantees test isolation regardless of fixture usage
import database
database.get_db().close()  # ensure module-level side effects run

from database import create_tables
create_tables()


@pytest.fixture(scope='module')
def app():
    """Create test Flask app with test database."""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
