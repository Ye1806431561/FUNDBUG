import os
import pytest
import tempfile
from unittest.mock import patch
from src.db.models import init_db, get_connection

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
    """Automatically patch get_connection in crud to use the test database."""
    # We patch the import in src.db.crud
    # Since crud.py does `from src.db.models import get_connection`, 
    # we can patch `src.db.crud.get_connection`
    
    def get_test_connection():
        return get_connection(test_db_path)
        
    with patch('src.db.crud.get_connection', side_effect=get_test_connection):
        yield
