"""tests/test_version_script.py – Regression tests for scripts/version.py.

Covers the destructive side effects fixed in v3.2.0:
  - ``_write_const`` must replace only the VERSION line, preserving the
    Nuitka workaround comments kept in const.py.
  - ``_write_pyproject`` must not reformat the TOML document (the old
    toml.dumps round-trip exploded inline dependency tables and added
    trailing commas everywhere).
  - ``set_version`` must keep .bumpversion.cfg's current_version in sync so
    a later ``--bump`` can still find the version string to replace.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import scripts.version as version_mod  # noqa: E402


@pytest.fixture()
def fake_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Materialize minimal copies of the three version-bearing files."""
    (tmp_path / "pyproject.toml").write_text(
        "[build-system]\n"
        'requires = ["poetry-core"]\n'
        'build-backend = "poetry.core.masonry.api"\n'
        "\n"
        "[tool.poetry]\n"
        'name = "test"\n'
        'version = "1.0.0"\n'
        'authors = ["A <a@example.com>"]\n'
        "\n"
        "[tool.poetry.dependencies]\n"
        'python = "^3.11"\n'
        'PySide6 = { version = ">=6.10.2,<7.0.0", python = ">=3.11,<3.15" }\n'
        "\n"
        "[tool.poetry.group.dev.dependencies]\n"
        'pytest = "^8.3.3"\n',
        encoding="utf-8",
    )
    const_dir = tmp_path / "ai_rom_batch_renamer" / "modules"
    const_dir.mkdir(parents=True)
    (const_dir / "const.py").write_text(
        'VERSION = "1.0.0"\n'
        "\n"
        "# ---------------------------------------------------------------------------\n"
        "# ALLOWED_REGION_CODES has been moved to platform_data\n"
        "# to work around a Nuitka <= 4.x + MSVC bug.\n"
        "# ---------------------------------------------------------------------------\n",
        encoding="utf-8",
    )
    (tmp_path / ".bumpversion.cfg").write_text(
        "[bumpversion]\ncurrent_version = 1.0.0\ncommit = False\ntag = False\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(version_mod, "_project_root", lambda: tmp_path)
    return tmp_path


class TestSetVersion:
    def test_const_preserves_comments(self, fake_project: Path):
        version_mod.set_version("2.0.0")
        text = (
            fake_project / "ai_rom_batch_renamer" / "modules" / "const.py"
        ).read_text(encoding="utf-8")
        assert 'VERSION = "2.0.0"' in text
        assert "ALLOWED_REGION_CODES has been moved" in text
        assert "Nuitka <= 4.x + MSVC bug" in text

    def test_pyproject_only_version_line_changes(self, fake_project: Path):
        before = (fake_project / "pyproject.toml").read_text(encoding="utf-8")
        version_mod.set_version("2.0.0")
        after = (fake_project / "pyproject.toml").read_text(encoding="utf-8")
        assert 'version = "2.0.0"' in after
        # Inline dependency table must stay inline (no reformat / no explosion)
        assert (
            'PySide6 = { version = ">=6.10.2,<7.0.0", python = ">=3.11,<3.15" }'
            in after
        )
        # No trailing-comma reformatting noise introduced by toml.dumps
        assert 'requires = ["poetry-core"]' in after
        # Only the version line itself may differ
        before_lines = before.splitlines()
        after_lines = after.splitlines()
        diffs = [
            (b, a) for b, a in zip(before_lines, after_lines, strict=True) if b != a
        ]
        assert diffs == [('version = "1.0.0"', 'version = "2.0.0"')]

    def test_bumpversion_cfg_stays_in_sync(self, fake_project: Path):
        version_mod.set_version("2.0.0")
        cfg = (fake_project / ".bumpversion.cfg").read_text(encoding="utf-8")
        assert "current_version = 2.0.0" in cfg

    def test_set_is_idempotent(self, fake_project: Path):
        version_mod.set_version("2.0.0")
        once = (fake_project / "pyproject.toml").read_text(encoding="utf-8")
        version_mod.set_version("2.0.0")
        twice = (fake_project / "pyproject.toml").read_text(encoding="utf-8")
        assert once == twice


class TestRegexUpdateVersion:
    def test_does_not_touch_inline_dependency_version(self):
        text = (
            "[tool.poetry]\n"
            'name = "x"\n'
            'version = "1.0.0"\n'
            "\n"
            "[tool.poetry.dependencies]\n"
            'PySide6 = { version = ">=6,<7" }\n'
        )
        out = version_mod._regex_update_version(text, "9.9.9")
        assert 'version = "9.9.9"' in out
        assert 'PySide6 = { version = ">=6,<7" }' in out

    def test_inserts_version_when_missing(self):
        text = '[tool.poetry]\nname = "x"\n'
        out = version_mod._regex_update_version(text, "3.2.0")
        assert 'version = "3.2.0"' in out


# ---------------------------------------------------------------------------
# PR review follow-ups (Kilo Code Review on #37)
# ---------------------------------------------------------------------------


class TestRunBump2VersionReturnCode:
    """A successful run must return 0 — ``return proc.returncode or 1`` turned
    every successful bump into a reported failure (``0 or 1`` == 1)."""

    def test_success_returns_zero(self, monkeypatch: pytest.MonkeyPatch):
        class FakeProc:
            returncode = 0

        monkeypatch.setattr(version_mod.subprocess, "run", lambda *a, **kw: FakeProc())
        assert version_mod._run_bump2version(["patch"]) == 0

    def test_failure_returns_actual_code(self, monkeypatch: pytest.MonkeyPatch):
        class FakeProc:
            returncode = 3

        monkeypatch.setattr(version_mod.subprocess, "run", lambda *a, **kw: FakeProc())
        assert version_mod._run_bump2version(["patch"]) == 3


class TestWriteGuards:
    """Failure in any compute step must leave ALL files untouched (two-phase
    set_version), never a half-synced pyproject/const pair."""

    def test_const_without_marker_aborts_writing_nothing(self, fake_project: Path):
        const_file = fake_project / "ai_rom_batch_renamer" / "modules" / "const.py"
        pyproject = fake_project / "pyproject.toml"
        const_file.write_text("# no VERSION marker here\n", encoding="utf-8")
        py_before = pyproject.read_text(encoding="utf-8")
        with pytest.raises(SystemExit):
            version_mod.set_version("2.0.0")
        # const.py untouched — and crucially pyproject.toml untouched too
        assert const_file.read_text(encoding="utf-8") == "# no VERSION marker here\n"
        assert pyproject.read_text(encoding="utf-8") == py_before

    def test_pyproject_not_written_when_parse_check_fails(
        self, fake_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        pyproject = fake_project / "pyproject.toml"
        const_file = fake_project / "ai_rom_batch_renamer" / "modules" / "const.py"
        py_before = pyproject.read_text(encoding="utf-8")
        const_before = const_file.read_text(encoding="utf-8")

        class BrokenToml:
            @staticmethod
            def loads(_s):
                raise ValueError("simulated TOML corruption")

        monkeypatch.setattr(version_mod, "toml", BrokenToml)
        with pytest.raises(SystemExit):
            version_mod.set_version("2.0.0")
        assert pyproject.read_text(encoding="utf-8") == py_before
        assert const_file.read_text(encoding="utf-8") == const_before

    def test_pyproject_not_written_when_version_mismatches(
        self, fake_project: Path, monkeypatch: pytest.MonkeyPatch
    ):
        pyproject = fake_project / "pyproject.toml"
        const_file = fake_project / "ai_rom_batch_renamer" / "modules" / "const.py"
        py_before = pyproject.read_text(encoding="utf-8")
        const_before = const_file.read_text(encoding="utf-8")

        class WrongToml:
            @staticmethod
            def loads(_s):
                # Parses fine, but reports a different version than requested —
                # the regex edit did not land where expected.
                return {"tool": {"poetry": {"version": "0.0.1"}}}

        monkeypatch.setattr(version_mod, "toml", WrongToml)
        with pytest.raises(SystemExit):
            version_mod.set_version("2.0.0")
        assert pyproject.read_text(encoding="utf-8") == py_before
        assert const_file.read_text(encoding="utf-8") == const_before
