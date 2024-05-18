import os
import unittest
from typing import List, Set

from util import static
from util.resource import VersionedResource


class TestResource(unittest.TestCase):
    """resource.py"""

    def writer(self, path: str, body: str) -> None:
        """write a file, track it for cleanup"""
        self.written.add(path)

        with open(path, 'w+') as fd:
            print(body, end='', file=fd)

    def setUp(self) -> None:
        self.written: Set[str] = set()
        self.writer('/tmp/versioned.bin', 'applesauce')

    def tearDown(self) -> None:
        for path in self.written:
            try:
                os.unlink(path)
            except OSError:
                pass

    def test_versioned_css(self) -> None:
        vr = VersionedResource(static.source_root + 'web/style.css')
        self.assertEqual(vr._name, 'style.css')
        self.assertIn('display: inline-block;', vr._body)
        self.assertEqual(len(vr._hash), 10)
        self.assertEqual(vr.path, f'style-{vr._hash}.css')

    def test_does_not_overwrite_identical(self) -> None:
        vr = VersionedResource('/tmp/versioned.bin', '/tmp')
        self.assertEqual(vr.path, '/tmp/versioned-404a6e35ea.bin')

        self.writer(vr.path, 'applesauce')
        vr.write()
        st1 = os.stat(vr.path)

        vr.write()
        vr.write()
        st2 = os.stat(vr.path)

        self.assertEqual(st1.st_mtime, st2.st_mtime)

    def test_finds_versions_with_glob(self) -> None:
        seen: List[str] = []

        for body in range(0, 10):
            self.writer('/tmp/versioned.bin', str(body))

            vr = VersionedResource('/tmp/versioned.bin', '/tmp')
            self.assertNotIn(vr.path, seen)
            seen.append(vr.path)

            self.written.add(vr.path)
            vr.write()

        self.assertEqual(len(seen), 10)
        self.assertEqual(vr.versions(), seen[::-1])

    def test_cleans_up_old_versions(self) -> None:
        wrote: List[str] = []

        for body in range(0, 10):
            self.writer('/tmp/versioned.bin', str(body))

            vr = VersionedResource('/tmp/versioned.bin', '/tmp')
            wrote.append(vr.path)

            self.written.add(vr.path)
            vr.write()

        self.assertEqual(len(vr.versions()), 10)
        vr.cleanup(3)

        retained = vr.versions()
        self.assertEqual(len(retained), 3)
        self.assertEqual(retained, wrote[-3:][::-1])


if __name__ == '__main__':
    unittest.main()
