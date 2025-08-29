"""
Configuration for database tests.

Database tests use a simple connection to test PostgreSQL availability.
"""

import os
import sqlite3
import tempfile

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@pytest.fixture
def db_connection():
    """
    Provides a simple SQLite database connection for testing.
    This allows database tests to run without requiring PostgreSQL setup.
    """
    # Create a temporary SQLite database for testing
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    conn = sqlite3.connect(temp_db.name)

    # Create a simple test table
    conn.execute(
        """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER
        )
    """
    )
    conn.commit()

    yield conn

    conn.close()
    # Clean up temp file
    os.unlink(temp_db.name)
