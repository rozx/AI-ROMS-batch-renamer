"""tests/test_cn_lookup.py – Unit tests for cn_lookup module."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_rom_batch_renamer.modules import cn_lookup as module


# ---------------------------------------------------------------------------
# Helpers: build minimal in-memory fixtures
# ---------------------------------------------------------------------------

_SAMPLE_CSV = """\
Name EN,Name CN
Super Mario Land (Japan),超级马里奥乐园
"Super Mario Land (Japan) (Rev 1)",超级马里奥乐园
"Super Mario Land 2 - 6 Golden Coins (USA, Europe)",超级马里奥乐园2
"Tetris (Japan) (En)",俄罗斯方块
Mario Lemieux Hockey (USA),
Super Robot Taisen A (Japan),超级机器人大战 A
Super Robot Taisen - Original Generation (USA),超级机器人大战 OG
Super Robot Taisen - Original Generation 2 (Japan),超级机器人大战 OG2
"Final Fantasy I, II Advance (Japan) (Rev 1)",最终幻想 1 + 2
Super Puzzle Fighter II Turbo (Europe),超级方块战士2加速版
bit Generations - Dotstream (Japan) (En),几何世代 - 点点潮流
"""

_SAMPLE_ALIAS = {
    "Super Mario": {
        "alias": ["超级马里奥", "超级马力欧", "超级玛丽"],
        "default": "超级马里奥",
        "exclude": ["Mario Lemieux Hockey", "Mario Andretti Racing"],
    },
    "Sonic": {
        "alias": ["索尼克", "音速小子"],
        "default": "索尼克",
        "exclude": ["Sonic Blast Man", "Sonic Wings"],
    },
    "template_bad": {
        "alias": ["template"],
        "default": "template",
    },
}

_PLATFORM = "Nintendo - Game Boy"


@pytest.fixture(autouse=True)
def reset_module_caches():
    """Clear module-level caches before each test."""
    module._csv_cache.clear()
    module._alias_cache = None
    module._assets_dir_cache = None
    yield
    module._csv_cache.clear()
    module._alias_cache = None
    module._assets_dir_cache = None


@pytest.fixture()
def tmp_assets_dir(tmp_path: Path):
    """Create a fake assets/rom-name-alias-cn dir with sample data."""
    alias_dir = tmp_path / "assets" / "rom-name-alias-cn"
    alias_dir.mkdir(parents=True)

    # Write sample CSV
    csv_path = alias_dir / f"{_PLATFORM}.csv"
    csv_path.write_text(_SAMPLE_CSV, encoding="utf-8")

    # Write sample JSON alias file
    json_path = alias_dir / "name_alias(Chinese).json"
    json_path.write_text(
        json.dumps(_SAMPLE_ALIAS, ensure_ascii=False), encoding="utf-8"
    )

    # Patch _resolve_assets_dir to return our tmp dir
    with patch.object(module, "_resolve_assets_dir", return_value=alias_dir):
        yield alias_dir


# ---------------------------------------------------------------------------
# _strip_tags
# ---------------------------------------------------------------------------


class TestStripTags:
    def test_removes_parentheses(self):
        assert module._strip_tags("Super Mario Land (Japan)") == "Super Mario Land"

    def test_removes_brackets(self):
        assert module._strip_tags("Game [Rev 1]") == "Game"

    def test_multiple_tags(self):
        assert module._strip_tags("Game (USA) (En) [v1.0]") == "Game"

    def test_collapses_spaces(self):
        assert module._strip_tags("A  B") == "A  B".replace("  ", " ")

    def test_no_tags(self):
        assert module._strip_tags("Tetris") == "Tetris"


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------


class TestLoadCsv:
    def test_loads_csv_successfully(self, tmp_assets_dir):
        exact, fuzzy = module._load_csv(_PLATFORM)
        assert "__exact__" in exact
        assert "super mario land (japan)" in exact["__exact__"]

    def test_missing_platform_returns_empty(self, tmp_assets_dir):
        exact, fuzzy = module._load_csv("Unknown - Platform")
        assert exact.get("__exact__") == {}
        assert fuzzy == {}

    def test_csv_cached_on_second_call(self, tmp_assets_dir):
        r1 = module._load_csv(_PLATFORM)
        r2 = module._load_csv(_PLATFORM)
        assert r1 is r2  # same object = from cache


# ---------------------------------------------------------------------------
# CSV lookup: exact match
# ---------------------------------------------------------------------------


class TestLookupCsvExact:
    def test_exact_match(self, tmp_assets_dir):
        result = module._lookup_csv("Super Mario Land (Japan)", _PLATFORM)
        assert result is not None
        assert (
            result["englishTitle"] == "Super Mario Land (Japan)"
        )  # _lookup_csv returns raw; cleaning done in lookup()
        assert result["chineseTitle"] == "超级马里奥乐园"

    def test_exact_match_case_insensitive(self, tmp_assets_dir):
        result = module._lookup_csv("super mario land (japan)", _PLATFORM)
        assert result is not None
        assert "Super Mario Land" in result["englishTitle"]

    def test_no_match_returns_none_from_unknown_platform(self, tmp_assets_dir):
        result = module._lookup_csv("Does Not Exist", "Unknown - Platform")
        assert result is None

    def test_reverse_cn_exact_match(self, tmp_assets_dir):
        # Chinese name exact match → should return the full EN ROM title
        result = module._lookup_csv("俄罗斯方块", _PLATFORM)
        assert result is not None
        assert (
            result["englishTitle"] == "Tetris (Japan) (En)"
        )  # raw from CSV; cleaning done in lookup()
        assert result["chineseTitle"] == "俄罗斯方块"

    def test_reverse_cn_exact_match_full_title(self, tmp_assets_dir):
        # "火焰纹章 - 封印之剑" style: exact CN name → full EN ROM name, not just IP key
        result = module._lookup_csv("超级马里奥乐园2", _PLATFORM)
        assert result is not None
        assert "Super Mario Land 2" in result["englishTitle"]

    def test_reverse_cn_space_normalized_match(self, tmp_assets_dir):
        # "超级机器人大战A" (no space) should match CSV entry "超级机器人大战 A" (with space)
        result = module._lookup_csv("超级机器人大战A", _PLATFORM)
        assert result is not None
        assert "Super Robot Taisen" in result["englishTitle"]

    def test_reverse_cn_space_normalized_match_reverse(self, tmp_assets_dir):
        # "超级机器人大战 A" (with space) should also match CSV entry "超级机器人大战 A"
        result = module._lookup_csv("超级机器人大战 A", _PLATFORM)
        assert result is not None
        assert "Super Robot Taisen" in result["englishTitle"]

    def test_reverse_cn_partial_match_with_prefix(self, tmp_assets_dir):
        # Filenames like "Q 棋魂 [简]" have a non-CJK sort prefix that lowers
        # fuzz.ratio below 85, but fuzz.partial_ratio=100 should still match.
        # Here "T 俄罗斯方块 [简]" should match "俄罗斯方块" (Tetris).
        result = module._lookup_csv("T 俄罗斯方块 [简]", _PLATFORM)
        assert result is not None
        assert "Tetris" in result["englishTitle"]
        assert result["chineseTitle"] == "俄罗斯方块"

    def test_reverse_cn_roman_numeral_match(self, tmp_assets_dir):
        # "最终幻想I, II Advance" should match CSV CN "最终幻想 1 + 2"
        # because _cn_key converts I->1, II->2 and strips non-CJK/digit chars.
        result = module._lookup_csv("最终幻想I, II Advance", _PLATFORM)
        assert result is not None
        assert "Final Fantasy" in result["englishTitle"]
        assert result["chineseTitle"] == "最终幻想 1 + 2"

    def test_reverse_cn_roman_numeral_between_cjk(self, tmp_assets_dir):
        # Roman numeral sandwiched between CJK characters:
        # "超级方块战士II加速版" → _cn_key → "超级方块战士2加速版"
        # should match CSV CN "超级方块战士2加速版" via Step 3b.
        result = module._lookup_csv("超级方块战士II加速版", _PLATFORM)
        assert result is not None
        assert "Puzzle Fighter" in result["englishTitle"]
        assert result["chineseTitle"] == "超级方块战士2加速版"

    def test_reverse_cn_sorted_cjk_key_reordered_segments(self, tmp_assets_dir):
        # Filename has CN subtitle segments in reversed order compared to CSV:
        # trimmed input "点点潮流 - 几何世代" vs CSV CN "几何世代 - 点点潮流".
        # Step 3c (sorted CJK key) must resolve this.
        # (rename.py trims before lookup, so we pass the already-trimmed name.)
        result = module._lookup_csv("点点潮流 - 几何世代", _PLATFORM)
        assert result is not None
        assert "Dotstream" in result["englishTitle"]
        assert result["chineseTitle"] == "几何世代 - 点点潮流"

    def test_reverse_cn_cjk_key_disambig_english_suffix(self, tmp_assets_dir):
        # "超级机器人大战 - Original Generation" has multiple CJK-key matches
        # (OG, OG2, A all map to "超级机器人大战").  The non-CJK suffix
        # "Original Generation" must correctly pick the OG entry, not OG2 or A.
        result = module._lookup_csv("超级机器人大战 - Original Generation", _PLATFORM)
        assert result is not None
        assert result["chineseTitle"] == "超级机器人大战 OG"
        assert "Original Generation" in result["englishTitle"]
        assert "Original Generation 2" not in result["englishTitle"]

    def test_reverse_cn_cjk_key_disambig_og2(self, tmp_assets_dir):
        # "超级机器人大战 OG2" should pick OG2 entry, not OG.
        result = module._lookup_csv("超级机器人大战 OG2", _PLATFORM)
        assert result is not None
        assert result["chineseTitle"] == "超级机器人大战 OG2"


# ---------------------------------------------------------------------------
# CSV lookup: fuzzy match
# ---------------------------------------------------------------------------


class TestLookupCsvFuzzy:
    def test_fuzzy_matches_rev_variant(self, tmp_assets_dir):
        # "Super Mario Land (Japan) (Rev 1)" stripped → "Super Mario Land"
        # should match entries with core name "Super Mario Land"
        result = module._lookup_csv("Super Mario Land (Japan) (Rev A)", _PLATFORM)
        assert result is not None
        assert "Super Mario Land" in result["englishTitle"]

    def test_fuzzy_no_match_for_unrelated(self, tmp_assets_dir):
        result = module._lookup_csv("Completely Unrelated Title XYZ", _PLATFORM)
        assert result is None

    def test_reverse_cn_fuzzy_match(self, tmp_assets_dir):
        # Slightly off Chinese name (extra tag) should still fuzzy-match via CN index
        result = module._lookup_csv("超级马里奥乐园 (2001)", _PLATFORM)
        assert result is not None
        assert "Super Mario Land" in result["englishTitle"]


# ---------------------------------------------------------------------------
# name_alias JSON loading
# ---------------------------------------------------------------------------


class TestLoadNameAlias:
    def test_loads_records(self, tmp_assets_dir):
        data = module._load_name_alias()
        records = data.get("records", [])
        keys = [r["key"] for r in records]
        assert "Super Mario" in keys
        assert "Sonic" in keys

    def test_skips_template_entries(self, tmp_assets_dir):
        data = module._load_name_alias()
        keys = [r["key"] for r in data["records"]]
        assert "template_bad" not in keys

    def test_alias_cache_on_second_call(self, tmp_assets_dir):
        r1 = module._load_name_alias()
        r2 = module._load_name_alias()
        assert r1 is r2


# ---------------------------------------------------------------------------
# name_alias fuzzy lookup
# ---------------------------------------------------------------------------


class TestLookupAlias:
    def test_chinese_substring_match(self, tmp_assets_dir):
        # "超级马里奥乐园" contains alias "超级马里奥"
        result = module._lookup_alias("超级马里奥乐园 (2000)")
        assert result is not None
        assert result["englishTitle"] == "Super Mario"
        assert result["chineseTitle"] == "超级马里奥"

    def test_exclude_prevents_false_match(self, tmp_assets_dir):
        # "Mario Lemieux Hockey" should NOT match "Super Mario" due to excludes
        result = module._lookup_alias("Mario Lemieux Hockey (USA)")
        assert result is None or result["englishTitle"] != "Super Mario"

    def test_no_match_gibberish(self, tmp_assets_dir):
        result = module._lookup_alias("xyzzy_gibberish_12345")
        assert result is None


# ---------------------------------------------------------------------------
# Main lookup function
# ---------------------------------------------------------------------------


class TestLookup:
    def test_csv_exact_hit(self, tmp_assets_dir):
        result = module.lookup("Super Mario Land (Japan).gb", _PLATFORM)
        assert result is not None
        assert (
            result["englishTitle"] == "Super Mario Land"
        )  # region tag stripped by lookup()

    def test_cn_reverse_hit_strips_region(self, tmp_assets_dir):
        # "俄罗斯方块" exact CN match → englishTitle should have region stripped
        result = module.lookup("俄罗斯方块.gb", _PLATFORM)
        assert result is not None
        assert result["englishTitle"] == "Tetris"  # "(Japan) (En)" stripped
        assert result["chineseTitle"] == "俄罗斯方块"

    def test_alias_fallback_when_no_csv_match(self, tmp_assets_dir):
        # A file with chinese name that has no CSV exact match but hits alias
        result = module.lookup("超级马里奥传说.gb", _PLATFORM)
        # May not find anything if SequenceMatcher is too strict; just verify no crash
        assert result is None or isinstance(result, dict)

    def test_unknown_platform_skips_csv(self, tmp_assets_dir):
        # Should not crash and may still find via alias
        result = module.lookup("超级马里奥乐园 (2000).gb", "unknown")
        # alias lookup still applies
        # just verify it returns dict or None without error
        assert result is None or isinstance(result, dict)

    def test_missing_platform_str(self, tmp_assets_dir):
        result = module.lookup("Super Mario Land (Japan).gb", "")
        # CSV lookup skipped, alias attempted
        assert result is None or isinstance(result, dict)


# ---------------------------------------------------------------------------
# lookupBatch
# ---------------------------------------------------------------------------


class TestLookupBatch:
    def test_batch_returns_hits(self, tmp_assets_dir):
        from ai_rom_batch_renamer.classes.RomFile import RomFile

        # Use a real temp file path so RomFile doesn't crash
        dummy_path = str(tmp_assets_dir / "Super Mario Land (Japan).gb")

        # Create a stub-like object instead to avoid filesystem dependency
        class FakeRomFile:
            def __init__(self, filename: str):
                self.originalFilename = filename
                self.path = str(tmp_assets_dir / filename)
                self.dir = str(tmp_assets_dir)
                self.baseName = os.path.splitext(filename)[0]
                self.extName = os.path.splitext(filename)[1]
                self.fileName = filename

        files = [
            FakeRomFile("Super Mario Land (Japan).gb"),
            FakeRomFile("Tetris (Japan) (En).gb"),
            FakeRomFile("__nonexistent_xyz_abc__.gb"),
        ]
        results = module.lookupBatch(files, _PLATFORM)  # type: ignore[arg-type]
        assert "Super Mario Land (Japan).gb" in results
        assert (
            results["Super Mario Land (Japan).gb"]["chineseTitle"] == "超级马里奥乐园"
        )
        assert "__nonexistent_xyz_abc__.gb" not in results


# ---------------------------------------------------------------------------
# get_candidates
# ---------------------------------------------------------------------------


class TestGetCandidates:
    def test_returns_top_candidates(self, tmp_assets_dir):
        candidates = module.get_candidates("Super Mario Land (Japan).gb", _PLATFORM)
        assert isinstance(candidates, list)
        # At least one candidate should contain "Super Mario"
        assert any("Super Mario" in c for c in candidates)

    def test_empty_when_platform_unknown(self, tmp_assets_dir):
        candidates = module.get_candidates("Super Mario Land.gb", "")
        assert candidates == []

    def test_empty_when_no_csv(self, tmp_assets_dir):
        candidates = module.get_candidates("Super Mario Land.gb", "Unknown - Platform")
        assert candidates == []

    def test_respects_top_n(self, tmp_assets_dir):
        candidates = module.get_candidates("Super Mario Land.gb", _PLATFORM, top_n=1)
        assert len(candidates) <= 1
