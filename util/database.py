'''
Database interface
'''

import copy
from typing import Any, Dict, List, Optional, Callable

from apocrypha.client import Client


class Database:
    '''Interface'''

    # High Level

    def get_image_hash(self, identifier: str) -> Optional[str]:
        '''Get an image's hash'''
        raise NotImplementedError

    def is_invalid_subject(self, key: str) -> bool:
        '''Check if this subject is in the invalid list'''
        raise NotImplementedError

    def get_mapped_subject(self, key: str) -> Optional[str]:
        '''Check if this subject is mapped to another name'''
        raise NotImplementedError

    def get_valid_subject(self, key: str) -> Optional[Dict[str, Any]]:
        '''Get the entry for this valid subject'''
        raise NotImplementedError

    # Low Level

    def get(
        self, *keys: str, default: Optional[Any] = None, cast: Optional[Callable] = None
    ) -> Any:
        '''Retrieve a value'''
        raise NotImplementedError

    def set(self, *keys: str, value: Any) -> None:
        '''Assign a value to a key'''
        raise NotImplementedError

    def delete(self, *keys: str) -> None:
        '''Delete a value'''
        raise NotImplementedError

    def keys(self, *keys: str) -> List[str]:
        '''Retrieve a list of keys'''
        raise NotImplementedError

    def append(self, *keys: str, value: Any) -> None:
        '''Append a value to a key'''
        raise NotImplementedError

    def remove(self, *keys: str, value: Any) -> None:
        '''Remove a value from a key'''
        raise NotImplementedError


class RealDatabase(Database):
    '''Real implementation that requires a database to be running'''

    def __init__(self) -> None:
        self.database = Client()
        self.hash_cache: Dict[str, Dict[str, str]] = {}
        self.wiki_cache: Dict[str, Any] = {}

    def _fill_hash_cache(self) -> None:
        '''populate the hash cache'''
        if not self.hash_cache:
            self.hash_cache = self.database.get('diving', 'cache')
            assert self.hash_cache

    def _fill_wiki_cache(self) -> None:
        '''populate the wiki cache'''
        if not self.wiki_cache:
            self.wiki_cache = self.database.get(
                'diving',
                'wikipedia',
            )
            assert self.wiki_cache

    def _invalidate_cache(self) -> None:
        '''invalidate the cache'''
        self.hash_cache = {}
        self.wiki_cache = {}

    def get_image_hash(self, identifier: str) -> Optional[str]:
        self._fill_hash_cache()
        return self.hash_cache.get(identifier, {}).get('hash')

    def is_invalid_subject(self, key: str) -> bool:
        self._fill_wiki_cache()
        return key in self.wiki_cache.get('invalid', [])

    def get_mapped_subject(self, key: str) -> Optional[str]:
        self._fill_wiki_cache()
        return self.wiki_cache['maps'].get(key)

    def get_valid_subject(self, key: str) -> Optional[Dict[str, Any]]:
        self._fill_wiki_cache()
        return copy.deepcopy(self.wiki_cache['valid'].get(key))

    def get(
        self, *keys: str, default: Optional[Any] = None, cast: Optional[Callable] = None
    ) -> Any:
        return self.database.get(*keys, default=default, cast=cast)

    def set(self, *keys: str, value: Any) -> None:
        self._invalidate_cache()
        self.database.set(*keys, value=value)

    def delete(self, *keys: str) -> None:
        self._invalidate_cache()
        self.database.delete(*keys)

    def keys(self, *keys: str) -> List[str]:
        return self.database.keys(*keys)

    def append(self, *keys: str, value: Any) -> None:
        self._invalidate_cache()
        self.database.append(*keys, value=value)

    def remove(self, *keys: str, value: Any) -> None:
        self._invalidate_cache()
        self.database.remove(*keys, value=value)


class TestDatabase(Database):
    '''Real implementation that requires a database to be running'''

    def __init__(self) -> None:
        pass

    def get_image_hash(self, identifier: str) -> Optional[str]:
        return 'test'

    def is_invalid_subject(self, key: str) -> bool:
        return True

    def get_mapped_subject(self, key: str) -> Optional[str]:
        return None

    def get_valid_subject(self, key: str) -> Optional[Dict[str, Any]]:
        return None

    def get(
        self, *keys: str, default: Optional[Any] = None, cast: Optional[Callable] = None
    ) -> Any:
        return 'test'

    def set(self, *keys: str, value: Any) -> None:
        pass

    def delete(self, *keys: str) -> None:
        pass

    def keys(self, *keys: str) -> List[str]:
        return []

    def append(self, *keys: str, value: Any) -> None:
        pass

    def remove(self, *keys: str, value: Any) -> None:
        pass


database: Database = RealDatabase()


def use_test_database() -> None:
    """Switch to TestDatabase"""
    # pylint: disable=global-statement
    global database
    database = TestDatabase()
