"""
Pytest configuration and fixtures for the diving test suite.
"""

import pytest

from diving.util import database


@pytest.fixture(autouse=True)
def use_test_db() -> None:
    """Switch to TestDatabase for all tests."""
    database.use_test_database()
