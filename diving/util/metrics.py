"""
An interface for other modules to record interesting information that can then
be displayed at the end of gallery.py's execution.
"""

from typing import Any


class Metrics:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def record(self, key: str, value: Any) -> None:
        self.data.setdefault(key, set())
        self.data[key].add(value)

    def counter(self, key: str, n: int = 1) -> None:
        self.data.setdefault(key, 0)
        self.data[key] += n

    def summary(self, label: str) -> None:
        if not self.data:
            return

        previous = self._restore(label)

        print('metrics...')
        last = []
        for key, value in sorted(self.data.items()):
            if isinstance(value, (set, list)):
                value = sorted(value)
                last.append(f'\t{key}: {value}')
            else:
                prev = previous.get(key, value)
                diff = value - prev
                diff = f'+{diff}' if diff >= 0 else f'{diff}'
                print(f'\t{value}\t{diff}\t{key}')

        print('')
        for line in sorted(last):
            print(line)

        self._persist(label)

    def _persist(self, label: str) -> None:
        from diving.util.database import database

        data = {}
        for k, v in self.data.items():
            if isinstance(v, int):
                data[k] = v
        database.set('diving', 'metrics', label, value=data)

    def _restore(self, label: str) -> dict[str, Any]:
        from diving.util.database import database

        return database.get('diving', 'metrics', label, default={})


metrics = Metrics()
