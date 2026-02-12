import os
import pytest
import tempfile
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.db.models import init_db, get_connection
from src.api.routes import router

@pytest.fixture
def app():
    """Create a FastAPI application for testing."""
    application = FastAPI()
    application.include_router(router)
    return application

@pytest.fixture
def client(app):
    """Create a TestClient for API testing."""
    return TestClient(app)

@pytest.fixture
def test_db_path():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize the database schema
    init_db(path)
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture(autouse=True)
def mock_db_connection(test_db_path):
    """Automatically patch get_connection in crud modules to use the test database."""
    def get_test_connection():
        return get_connection(test_db_path)
    
    # Patch in all sub-modules where get_connection is used
    p1 = patch('src.db.crud_funds.get_connection', side_effect=get_test_connection)
    p2 = patch('src.db.crud_holdings.get_connection', side_effect=get_test_connection)
    p3 = patch('src.db.crud_nav.get_connection', side_effect=get_test_connection)
    p4 = patch('src.db.crud_watchlist.get_connection', side_effect=get_test_connection)
    # Also patch the source model for tests that use it directly
    p5 = patch('src.db.models.get_connection', side_effect=get_test_connection)
        
    with p1, p2, p3, p4, p5:
        yield
