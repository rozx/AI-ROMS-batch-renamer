"""tests/test_region_detection.py – Unit tests for region detection logic.

Covers:
- utils.getRegion() canonical mapping
- regionMatchRegex / chineseMatchRegex patterns
- rename() dry-run integration: region must come from original filename,
  not be overwritten by a Chinese title returned from cn_lookup / AI.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import regex

from ai_rom_batch_renamer.modules import utils as utilsModule
from ai_rom_batch_renamer.modules import regex as regexModule
from ai_rom_batch_renamer.modules.rename import rename


# ---------------------------------------------------------------------------
# utils.getRegion()
# ---------------------------------------------------------------------------


class TestGetRegion:
    @pytest.mark.parametrize(
        "tag,expected",
        [
            # US variants
            ("US", "US"),
            ("us", "US"),
            ("USA", "US"),
            ("usa", "US"),
            # JP variants
            ("JP", "JP"),
            ("jp", "JP"),
            ("Japan", "JP"),
            # EU variants
            ("EU", "EU"),
            ("eu", "EU"),
            ("Europe", "EU"),
            # Simplified Chinese variants
            ("简", "简"),
            ("简体", "简"),
            ("简體", "简"),
            ("简中", "简"),
            ("中文", "简"),
            ("SC", "简"),
            ("sc", "简"),
            # Traditional Chinese variants
            ("繁", "繁"),
            ("繁体", "繁"),
            ("繁體", "繁"),
            ("繁中", "繁"),
            ("TC", "繁"),
            ("tc", "繁"),
            # Combined
            ("简&繁", "简&繁"),
            ("简繁", "简&繁"),
            ("繁简", "简&繁"),
            ("SC&TC", "简&繁"),
            ("sc&tc", "简&繁"),
            # World / UE
            ("World", "WW"),
            ("WW", "WW"),
            ("ww", "WW"),
            ("UE", "UE"),
            ("ue", "UE"),
            # GoodTools single-letter codes
            ("U", "US"),
            ("J", "JP"),
            ("E", "EU"),
            ("C", "简"),
            ("Unk", "WW"),
            ("unk", "WW"),
        ],
    )
    def test_known_tags(self, tag: str, expected: str):
        assert utilsModule.getRegion(tag) == expected

    def test_unknown_tag_returns_input_unchanged(self):
        # getRegionFromRegionDictList returns the input string as-is when not matched
        assert utilsModule.getRegion("Unknown") == "Unknown"
        assert utilsModule.getRegion("ZZ") == "ZZ"
        assert utilsModule.getRegion("") == ""


# ---------------------------------------------------------------------------
# regionMatchRegex – pattern matching on filenames
# ---------------------------------------------------------------------------


class TestRegionMatchRegex:
    @pytest.mark.parametrize(
        "filename,expected_tag",
        [
            ("Super Mario (USA).nes", "USA"),
            ("Kirby [JP].gba", "JP"),
            ("Final Fantasy [Europe].sfc", "Europe"),
            ("Sonic [简].md", "简"),
            ("Zelda [繁].sfc", "繁"),
            ("Game [SC].gba", "SC"),
            ("Game [TC].gba", "TC"),
            ("Game [WW].gba", "WW"),
            ("Game [UE].gba", "UE"),
            ("Game [简&繁].gba", "简&繁"),
            ("Game [SC&TC].gba", "SC&TC"),
            # GoodTools single-letter codes
            ("国际大奖赛II(E).sfc", "E"),
            ("Contra (U).nes", "U"),
            ("魔界村 (J).nes", "J"),
            ("Game (C).gba", "C"),
            ("Game (Unk).sfc", "Unk"),
            ("Game (unk).sfc", "unk"),
        ],
    )
    def test_region_tag_extracted(self, filename: str, expected_tag: str):
        m = regex.search(regexModule.regionMatchRegex, filename)
        assert m is not None, f"Expected match in '{filename}'"
        assert m.group(0) == expected_tag

    @pytest.mark.parametrize(
        "tag,expected_canonical",
        [
            ("国际大奖赛II(E).sfc", "EU"),
            ("Contra (U).nes", "US"),
            ("Super Mario (J).nes", "JP"),
            ("Game (C).gba", "简"),
            ("Game (Unk).sfc", "WW"),
        ],
    )
    def test_goodtools_codes_map_to_canonical(self, tag: str, expected_canonical: str):
        """Single-letter GoodTools codes extracted from filename must map to canonical region."""
        m = regex.search(regexModule.regionMatchRegex, tag)
        assert m is not None, f"Expected region match in '{tag}'"
        assert utilsModule.getRegion(m.group(0)) == expected_canonical

    @pytest.mark.parametrize(
        "filename",
        [
            "Super Mario.nes",  # no region tag
            "Game (2005).gba",  # year, not region
            "Game [Hack].nes",  # hack tag
            "Game [Unknown].sfc",  # unknown string
        ],
    )
    def test_no_region_tag(self, filename: str):
        m = regex.search(regexModule.regionMatchRegex, filename)
        assert m is None, f"Expected no match in '{filename}'"


# ---------------------------------------------------------------------------
# chineseMatchRegex – 汉化 / 润色 keywords
# ---------------------------------------------------------------------------


class TestChineseMatchRegex:
    @pytest.mark.parametrize(
        "filename",
        [
            "Super Mario (汉化).nes",
            "Game 汉化版.sfc",
            "Contra 润色.nes",
        ],
    )
    def test_matches_chinese_keywords(self, filename: str):
        assert regex.search(regexModule.chineseMatchRegex, filename) is not None

    @pytest.mark.parametrize(
        "filename",
        [
            "Super Mario (Japan).nes",
            "超级马里奥.nes",  # CJK title only – no 汉化/润色
            "Game [简].sfc",  # region tag, not keyword
        ],
    )
    def test_no_false_positives(self, filename: str):
        assert regex.search(regexModule.chineseMatchRegex, filename) is None


# ---------------------------------------------------------------------------
# rename() dry-run integration tests for region detection
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_rom_file(tmp_path: Path):
    """Return a factory that creates a dummy ROM file in tmp_path."""

    def _make(name: str) -> str:
        path = tmp_path / name
        path.write_bytes(b"\x00" * 16)
        return str(path)

    return _make


class TestRenameRegionFromOriginalFilename:
    """Ensure region is always extracted from the original filename.

    When cn_lookup or AI returns a Chinese title, that should NOT force the
    region to [简].  The region must come exclusively from the original filename.
    """

    def _run_dry(
        self,
        file_path: str,
        cn_result: dict | None = None,
        platform: str = "Nintendo - Game Boy Advance",
    ) -> str:
        """Run rename in dry-run mode and return the resulting filename."""
        mock_lookup = {os.path.basename(file_path): cn_result} if cn_result else {}

        with patch(
            "ai_rom_batch_renamer.modules.rename.cnLookupModule.lookupBatch",
            return_value=mock_lookup,
        ):
            rename(
                {
                    "files": file_path,
                    "dir": "",
                    "trim": False,
                    "dry": True,
                    "pinyin": False,
                    "includes": [],
                    "excludes": [],
                    "output": False,
                    "recursive": False,
                    "unzip": False,
                    "pwd": "",
                    "ai": False,
                    "model": "",
                    "apiKey": "",
                    "endpoint": "",
                    "tavilyApiKey": "",
                    "platform": platform,
                    "ai_batch_size": 10,
                    "ai_no_cache": True,
                    "force": True,
                    "cn_lookup": bool(cn_result),
                }
            )

        from ai_rom_batch_renamer.classes.RomFile import RomFile

        rf = RomFile(file_path)
        # Re-derive result filename the same way rename() would: read the dir
        dir_ = os.path.dirname(file_path)
        candidates = os.listdir(dir_)
        # The dry-run leaves the original file unchanged on disk.
        # Return whichever candidate differs from the original (if any),
        # otherwise fall back to the original.
        orig = os.path.basename(file_path)
        non_orig = [c for c in candidates if c != orig]
        return non_orig[0] if non_orig else orig

    # ---- Helper that inspects the RomFile directly after rename ----

    def _renamed_basename(
        self,
        file_path: str,
        cn_result: dict | None = None,
        platform: str = "Nintendo - Game Boy Advance",
    ) -> str:
        """Run rename dry-run and return the target baseName via RomFile."""
        from ai_rom_batch_renamer.classes.RomFile import RomFile
        from ai_rom_batch_renamer.modules.rename import (
            rename as _rename,
            RomFile as _RF,
        )

        captured: list[str] = []

        original_rename_files = __import__(
            "ai_rom_batch_renamer.modules.rename", fromlist=["renameFiles"]
        ).renameFiles

        def fake_rename_files(pending, romFile, dry, renamed, os_plat):
            captured.append(romFile.fileName)
            return [romFile.fileName]

        mock_lookup = {os.path.basename(file_path): cn_result} if cn_result else {}

        with (
            patch(
                "ai_rom_batch_renamer.modules.rename.cnLookupModule.lookupBatch",
                return_value=mock_lookup,
            ),
            patch(
                "ai_rom_batch_renamer.modules.rename.renameFiles",
                side_effect=fake_rename_files,
            ),
        ):
            _rename(
                {
                    "files": file_path,
                    "dir": "",
                    "trim": False,
                    "dry": True,
                    "pinyin": False,
                    "includes": [],
                    "excludes": [],
                    "output": False,
                    "recursive": False,
                    "unzip": False,
                    "pwd": "",
                    "ai": False,
                    "model": "",
                    "apiKey": "",
                    "endpoint": "",
                    "tavilyApiKey": "",
                    "platform": platform,
                    "ai_batch_size": 10,
                    "ai_no_cache": True,
                    "force": True,
                    "cn_lookup": bool(cn_result),
                }
            )

        return captured[0] if captured else ""

    def test_us_region_preserved_when_cn_lookup_returns_chinese_title(
        self, tmp_rom_file
    ):
        """File tagged [US] must stay [US] even when cn_lookup returns a Chinese title."""
        path = tmp_rom_file("Super Robot Wars (USA).gba")
        result = self._renamed_basename(
            path,
            cn_result={
                "englishTitle": "Super Robot Wars",
                "chineseTitle": "超级机器人大战",
            },
        )
        assert "[US]" in result, f"Expected [US] in result, got: {result}"
        assert (
            "[简]" not in result
        ), f"[简] must not appear when original has [US], got: {result}"

    def test_jp_region_preserved_when_cn_lookup_returns_chinese_title(
        self, tmp_rom_file
    ):
        """File tagged (Japan) must produce [JP], not [简]."""
        path = tmp_rom_file("Super Robot Taisen A (Japan).gba")
        result = self._renamed_basename(
            path,
            cn_result={
                "englishTitle": "Super Robot Wars A",
                "chineseTitle": "超级机器人大战 A",
            },
        )
        assert "[JP]" in result, f"Expected [JP] in result, got: {result}"
        assert (
            "[简]" not in result
        ), f"[简] must not appear when original has (Japan), got: {result}"

    def test_no_region_tag_no_chinese_keyword_yields_no_region(self, tmp_rom_file):
        """File with no region tag and no Chinese keyword → no region appended,
        even when cn_lookup returns a Chinese title."""
        path = tmp_rom_file("Kirby Amazing Mirror.gba")
        result = self._renamed_basename(
            path,
            cn_result={
                "englishTitle": "Kirby: Amazing Mirror",
                "chineseTitle": "星之卡比 镜中奇境",
            },
        )
        assert (
            "[简]" not in result
        ), f"[简] must not be inferred from Chinese title, got: {result}"
        assert "[US]" not in result
        assert "[JP]" not in result

    def test_simplified_chinese_tag_in_filename_preserved(self, tmp_rom_file):
        """File explicitly tagged [简] keeps [简] after cn_lookup enrichment."""
        path = tmp_rom_file("Contra [简].nes")
        result = self._renamed_basename(
            path,
            cn_result={"englishTitle": "Contra", "chineseTitle": "魂斗罗"},
        )
        assert "[简]" in result, f"Expected [简] in result, got: {result}"

    def test_hanhua_keyword_in_filename_yields_simplified_region(self, tmp_rom_file):
        """File containing '汉化' keyword → [简] even without an explicit region tag."""
        path = tmp_rom_file("Contra 汉化.nes")
        result = self._renamed_basename(path, cn_result=None)
        assert "[简]" in result, f"Expected [简] for hanhua file, got: {result}"

    def test_eu_region_tag_not_overwritten(self, tmp_rom_file):
        """File tagged [EU] must keep [EU] even with a Chinese enrichment result."""
        path = tmp_rom_file("Tetris (Europe).gb")
        result = self._renamed_basename(
            path,
            cn_result={"englishTitle": "Tetris", "chineseTitle": "俄罗斯方块"},
        )
        assert "[EU]" in result, f"Expected [EU] in result, got: {result}"
        assert "[简]" not in result

    def test_traditional_chinese_tag_preserved(self, tmp_rom_file):
        """File with [繁] keeps [繁] and does not mutate to [简]."""
        path = tmp_rom_file("Final Fantasy [繁].sfc")
        result = self._renamed_basename(
            path,
            cn_result={"englishTitle": "Final Fantasy", "chineseTitle": "最终幻想"},
        )
        assert "[繁]" in result, f"Expected [繁] in result, got: {result}"
        assert "[简]" not in result
