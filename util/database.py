'''
Database interface
'''

import copy
from typing import Any, Dict, List, Optional

import apocrypha.client

from util.metrics import metrics


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

    def get(self, *keys: str, default: Optional[Any] = None) -> Any:
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
        self.database = apocrypha.client.Client()
        self.level_cache: Dict[str, Any] = {}

    def _invalidate_cache(self) -> None:
        '''invalidate the cache'''
        self.level_cache = {}

    def get_image_hash(self, identifier: str) -> Optional[str]:
        return self.get('diving', 'cache', identifier, default={}).get('hash')

    def is_invalid_subject(self, key: str) -> bool:
        values = self.get('diving', 'wikipedia', 'invalid')
        return key in values

    def get_mapped_subject(self, key: str) -> Optional[str]:
        return self.get('diving', 'wikipedia', 'maps', key)

    def get_valid_subject(self, key: str) -> Optional[Dict[str, Any]]:
        value = self.get('diving', 'wikipedia', 'valid', key)
        return copy.deepcopy(value)

    def get(self, *keys: str, default: Optional[Any] = None) -> Any:
        *context, target = keys
        ckey = ' '.join(context)

        if ckey not in self.level_cache:
            metrics.counter('database gets')
            value = self.database.get(*context, default={})
            assert isinstance(value, dict), f'{ckey} is not a dictionary'
            self.level_cache[ckey] = self.database.get(*context)

        return self.level_cache[ckey].get(target, default)

    def set(self, *keys: str, value: Any) -> None:
        self._invalidate_cache()
        metrics.counter('database sets')
        self.database.set(*keys, value=value)

    def delete(self, *keys: str) -> None:
        metrics.counter('database dels')
        self._invalidate_cache()
        self.database.delete(*keys)

    def keys(self, *keys: str) -> List[str]:
        metrics.counter('database keys')
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

    def get(self, *keys: str, default: Optional[Any] = None) -> Any:
        return None

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
    global database
    database = TestDatabase()
