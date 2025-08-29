"""
Database connection tests.

Tests to verify database connectivity and basic operations using SQLite.
"""


def test_database_connection_exists(db_connection):
    """Test that we can connect to the database."""
    assert db_connection is not None

    # Test basic query
    cursor = db_connection.cursor()
    cursor.execute("SELECT sqlite_version()")
    version = cursor.fetchone()
    cursor.close()

    assert version is not None
    assert version[0] is not None


def test_database_basic_operations(db_connection):
    """Test basic database operations (INSERT, SELECT, DELETE)."""
    cursor = db_connection.cursor()

    try:
        # Insert test data into the pre-created test_table
        cursor.execute(
            "INSERT INTO test_table (name, value) VALUES (?, ?)", ("test_entry", 42)
        )
        db_connection.commit()

        # Query the data
        cursor.execute(
            "SELECT name, value FROM test_table WHERE name = ?", ("test_entry",)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "test_entry"
        assert result[1] == 42

        # Clean up
        cursor.execute("DELETE FROM test_table WHERE name = ?", ("test_entry",))
        db_connection.commit()

    except Exception as e:
        db_connection.rollback()
        raise e
    finally:
        cursor.close()


def test_database_transaction_rollback(db_connection):
    """Test that database transactions can be rolled back properly."""
    cursor = db_connection.cursor()

    try:
        # Insert data that we'll rollback
        cursor.execute(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("should_be_rolled_back", 999),
        )

        # Rollback the transaction
        db_connection.rollback()

        # Verify the data was not committed
        cursor.execute(
            "SELECT COUNT(*) FROM test_table WHERE name = ?",
            ("should_be_rolled_back",),
        )
        count = cursor.fetchone()[0]

        assert count == 0, "Transaction was not properly rolled back"

    except Exception as e:
        db_connection.rollback()
        raise e
    finally:
        cursor.close()
