"""
Database interface
"""

from typing import Any, Dict, List, Optional

import apocrypha.client

from diving.util.metrics import metrics


class Database:
    """Interface"""

    # High Level

    def get_image_hash(self, identifier: str) -> Optional[str]:
        """Get an image's hash"""
        raise NotImplementedError

    # Low Level

    def get(self, *keys: str, default: Optional[Any] = None) -> Any:
        """Retrieve a value"""
        raise NotImplementedError

    def set(self, *keys: str, value: Any) -> None:
        """Assign a value to a key"""
        raise NotImplementedError

    def delete(self, *keys: str) -> None:
        """Delete a value"""
        raise NotImplementedError

    def keys(self, *keys: str) -> List[str]:
        """Retrieve a list of keys"""
        raise NotImplementedError

    def append(self, *keys: str, value: Any) -> None:
        """Append a value to a key"""
        raise NotImplementedError

    def remove(self, *keys: str, value: Any) -> None:
        """Remove a value from a key"""
        raise NotImplementedError


class RealDatabase(Database):
    """Real implementation that requires a database to be running"""

    def __init__(self) -> None:
        self.database = apocrypha.client.Client()
        self.level_cache: Dict[str, Any] = {}

    def _invalidate_cache(self) -> None:
        """invalidate the cache"""
        self.level_cache = {}

    def get_image_hash(self, identifier: str) -> Optional[str]:
        return self.get('diving', 'cache', identifier, default={}).get('hash')

    def get(self, *keys: str, default: Optional[Any] = None) -> Any:
        *context, target = keys
        ckey = ' '.join(context)

        if ckey not in self.level_cache:
            metrics.counter('database gets')
            value = self.database.get(*context, default={})
            assert isinstance(value, dict), f'{ckey} is not a dictionary'
            self.level_cache[ckey] = value

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
    """Real implementation that requires a database to be running"""

    def __init__(self) -> None:
        pass

    def get_image_hash(self, identifier: str) -> Optional[str]:
        return 'test'

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
