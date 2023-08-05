'''
An interface for other modules to record interesting information that can then
be displayed at the end of gallery.py's execution.
'''

from typing import Any


class Metrics:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def record(self, key: str, value: Any) -> None:
        self.data.setdefault(key, set())
        self.data[key].add(value)

    def counter(self, key: str) -> None:
        self.data.setdefault(key, 0)
        self.data[key] += 1

    def summary(self) -> None:
        if not self.data:
            return

        print('metrics...')
        last = []
        for key, value in sorted(self.data.items()):
            if isinstance(value, (set, list)):
                value = sorted(value)
                last.append(f'\t{key}: {value}')
            else:
                print(f'\t{value}\t{key}')

        print('')
        for line in sorted(last):
            print(line)


metrics = Metrics()
