import os
from pathlib import Path

from diving.util import static
from diving.util.resource import VersionedResource


class TestResource:
    """resource.py"""

    def test_versioned_css(self) -> None:
        vr = VersionedResource(static.source_root + 'web/style.css')
        assert vr._name == 'style.css'
        assert 'display: inline-block;' in vr._body
        assert len(vr._hash) == 10
        assert vr.path == f'style-{vr._hash}.css'

    def test_does_not_overwrite_identical(self, tmp_path: Path) -> None:
        source = tmp_path / 'versioned.bin'
        source.write_text('applesauce')

        vr = VersionedResource(str(source), str(tmp_path))
        assert vr.path == str(tmp_path / 'versioned-404a6e35ea.bin')

        Path(vr.path).write_text('applesauce')
        vr.write()
        st1 = os.stat(vr.path)

        vr.write()
        vr.write()
        st2 = os.stat(vr.path)

        assert st1.st_mtime == st2.st_mtime

    def test_finds_versions_with_glob(self, tmp_path: Path) -> None:
        source = tmp_path / 'versioned.bin'
        seen: list[str] = []

        for body in range(0, 10):
            source.write_text(str(body))

            vr = VersionedResource(str(source), str(tmp_path))
            assert vr.path not in seen
            seen.append(vr.path)
            vr.write()

        assert len(seen) == 10
        assert vr.versions() == seen[::-1]

    def test_cleans_up_old_versions(self, tmp_path: Path) -> None:
        source = tmp_path / 'versioned.bin'
        wrote: list[str] = []

        for body in range(0, 10):
            source.write_text(str(body))

            vr = VersionedResource(str(source), str(tmp_path))
            wrote.append(vr.path)
            vr.write()

        assert len(vr.versions()) == 10
        vr.cleanup(3)

        retained = vr.versions()
        assert len(retained) == 3
        assert retained == wrote[-3:][::-1]
