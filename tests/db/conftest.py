"""
Configuration for database tests.

Database tests require a PostgreSQL instance and test database isolation.
"""
import os
import psycopg2
import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def db_test_setup():
    """
    Setup for database tests.
    
    Ensures PostgreSQL is available and creates test database if needed.
    """
    load_dotenv(".env.test", override=True)
    
    # Database connection parameters
    db_host = "localhost"
    db_port = "5432" 
    db_user = os.getenv("DB_USER", "django_user")
    db_password = os.getenv("DB_PASSWORD", "django_password")
    db_name = os.getenv("DB_NAME", "django_db_test")
    
    # Wait for PostgreSQL to be ready and create test database if needed
    try:
        # Connect to postgres default database first
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create test database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name}")
            
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        pytest.fail(f"Failed to setup database for tests: {e}")
    
    yield
    

@pytest.fixture
def db_connection():
    """
    Provides a database connection for individual tests.
    """
    db_host = "localhost"
    db_port = "5432"
    db_user = os.getenv("DB_USER", "django_user")
    db_password = os.getenv("DB_PASSWORD", "django_password")
    db_name = os.getenv("DB_NAME", "django_db_test")
    
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    yield conn
    
    conn.close()