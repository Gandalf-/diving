'''
Database interface
'''

from typing import Any, List

from apocrypha.client import Client


class Database:
    '''Interface'''

    def get(self, *keys, default=None, cast=None) -> Any:
        '''Retrieve a value'''
        raise NotImplementedError

    def set(self, *keys, value) -> None:
        '''Assign a value to a key'''
        raise NotImplementedError

    def delete(self, *keys) -> None:
        '''Delete a value'''
        raise NotImplementedError

    def keys(self, *keys) -> List[str]:
        '''Retrieve a list of keys'''
        raise NotImplementedError

    def append(self, *keys, value) -> None:
        '''Append a value to a key'''
        raise NotImplementedError

    def remove(self, *keys, value) -> None:
        '''Remove a value from a key'''
        raise NotImplementedError


class RealDatabase(Database):
    '''Real implementation that requires a database to be running'''

    def __init__(self) -> None:
        self.database = Client()

    def get(self, *keys, default=None, cast=None) -> Any:
        return self.database.get(*keys, default=default, cast=cast)

    def set(self, *keys, value) -> None:
        self.database.set(*keys, value=value)

    def delete(self, *keys) -> None:
        self.database.delete(*keys)

    def keys(self, *keys) -> List[str]:
        return self.database.keys(*keys)

    def append(self, *keys, value) -> None:
        self.database.append(*keys, value=value)

    def remove(self, *keys, value) -> None:
        self.database.remove(*keys, value=value)


class TestDatabase(Database):
    '''Real implementation that requires a database to be running'''

    def __init__(self) -> None:
        pass

    def get(self, *keys, default=None, cast=None) -> Any:
        return 'test'

    def set(self, *keys, value) -> None:
        pass

    def delete(self, *keys) -> None:
        pass

    def keys(self, *keys) -> List[str]:
        return []

    def append(self, *keys, value) -> None:
        pass

    def remove(self, *keys, value) -> None:
        pass


database = RealDatabase()


def use_test_database():
    """Switch to TestDatabase"""
    # pylint: disable=global-statement
    global database
    database = TestDatabase()
