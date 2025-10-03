"""
Base repository with connection management and common utilities.
"""
import sqlite3
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager


class BaseRepository:
    """Base repository with shared database connection logic."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize repository.

        Args:
            db_path: Path to SQLite database. Defaults to /var/data/tutorial_customer.db
        """
        self.db_path = db_path or Path("/var/data/tutorial_customer.db")

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection with row factory enabled
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """
        Execute SELECT query and return all results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of Row objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_query_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Execute SELECT query and return single result.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single Row object or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def execute_command(self, command: str, params: tuple = ()) -> int:
        """
        Execute INSERT/UPDATE/DELETE command.

        Args:
            command: SQL command string
            params: Command parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(command, params)
            conn.commit()
            return cursor.rowcount

    def execute_command_with_lastrowid(self, command: str, params: tuple = ()) -> int:
        """
        Execute INSERT command and return last row ID.

        Args:
            command: SQL INSERT command
            params: Command parameters

        Returns:
            Last inserted row ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(command, params)
            conn.commit()
            return cursor.lastrowid
