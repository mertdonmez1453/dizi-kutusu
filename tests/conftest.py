import os
import sys
import pytest
import time

# Proje kök dizinini PYTHONPATH'e ekle
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from app import create_app
from app.db import db
import logging

# Disable SQLAlchemy SQL echoing explicitly for tests globally
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_ECHO": False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

_start_time = 0.0

def pytest_sessionstart(session):
    global _start_time
    _start_time = time.time()
    from tests.logger import init_test_run
    from tests.scenario_logger import init_scenario_run
    init_test_run()
    init_scenario_run()

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    global _start_time
    if _start_time > 0.0:
        total_time = time.time() - _start_time
        terminalreporter.write_line("\n" + "="*55)
        terminalreporter.write_line(f"[RESULT] ALL TESTS COMPLETED IN {total_time:.3f} SECONDS")
        terminalreporter.write_line("="*55 + "\n")
