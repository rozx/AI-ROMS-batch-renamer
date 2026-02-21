"""cn_lookup.py – Local Chinese/English ROM title lookup.

Uses platform CSV files from assets/rom-name-alias-cn/:
  1. Platform CSV files (Name EN, Name CN columns) from rom-name-cn project.

The directory may also contain name_alias(Chinese).json with common
Chinese alias ↔ English IP key mappings, but this file is not currently
consulted by the public ``lookup()`` function.

Lookup priority per file (current behavior of ``lookup()``):
  Step 1 – CSV exact match (baseName == Name EN)
  Step 2 – CSV fuzzy match (strip bracket-tags, rapidfuzz ratio ≥ 85)
  Step 3 – CSV exact match against Name CN (when baseName contains CJK chars)
  Step 3b – CSV CJK+digit key match (Roman→Arabic, strips non-CJK noise)
  Step 4 – CSV fuzzy match against Name CN (ratio ≥ 85)
  Step 4b – CSV partial_ratio match against Name CN (partial ≥ 90)

When a match is found, results are returned as
``{"englishTitle": str, "chineseTitle": str}``, matching the format
returned by the AI module.  If no CSV match is found, ``lookup()``
returns ``None``.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from rapidfuzz import fuzz, process as fuzz_process
from rich import print as rprint

if TYPE_CHECKING:
    from ai_rom_batch_renamer.classes.RomFile import RomFile


class CsvIndexes(TypedDict):
    """Structured indexes built from a platform CSV file."""

    __exact__: dict[str, str]  # name_en_lower -> name_cn
    __exact_orig__: dict[str, str]  # name_en_lower -> original name_en
    __cn_exact__: dict[str, dict[str, str]]  # normalized_cn -> {name_en, name_cn}
    __cn_fuzzy__: dict[
        str, list[dict[str, str]]
    ]  # stripped_cn_lower -> [{name_en, name_cn}, ...]
    __cn_cjk_key__: dict[
        str, list[dict[str, str]]
    ]  # _cn_key(name_cn) -> [{name_en, name_cn}, ...]
    __cn_sorted_cjk_key__: dict[
        str, list[dict[str, str]]
    ]  # sorted(_cn_key) -> [{name_en, name_cn}, ...]


# ---------------------------------------------------------------------------
# Module-level caches (avoid re-loading the same files repeatedly)
# ---------------------------------------------------------------------------
_csv_cache: dict[str, tuple[CsvIndexes, dict[str, list[dict]]]] = {}

_EMPTY_INDEXES: CsvIndexes = CsvIndexes(
    __exact__={},
    __exact_orig__={},
    __cn_exact__={},
    __cn_fuzzy__={},
    __cn_cjk_key__={},
    __cn_sorted_cjk_key__={},
)
_alias_cache: dict | None = None
_assets_dir_cache: Path | None = None

# Regex to strip bracket tags: (…) […] {…}
_TAGS_RE = re.compile(r"[\(\[\{][^\)\]\}]*[\)\]\}]")

# Region preference: prefer (USA) > (World) > others
_US_REGION_RE = re.compile(r"\(USA\)", re.IGNORECASE)
_WORLD_REGION_RE = re.compile(r"\(World\)", re.IGNORECASE)


def _us_region_score(entry: dict) -> int:
    """Return a US-region preference score (higher = more preferred).

    USA=2, World=1, others=0.
    Used as a tiebreaker so that when multiple English titles share the same
    Chinese title, the US region version is returned.
    """
    name_en = entry.get("name_en", "")
    if _US_REGION_RE.search(name_en):
        return 2
    if _WORLD_REGION_RE.search(name_en):
        return 1
    return 0


def _prefer_us(entries: list[dict]) -> dict:
    """Pick the US/World region entry from a list of candidates.

    Falls back gracefully to the first entry when no US/World entry exists.
    """
    if len(entries) == 1:
        return entries[0]
    return max(entries, key=_us_region_score)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _resolve_assets_dir() -> Path | None:
    """Locate the assets/rom-name-alias-cn directory.

    Searches in order:
      1. Relative to this source file (development / Poetry install).
      2. Relative to sys.executable parent (Nuitka onefile extracted temp dir).
      3. Current working directory.
    """
    global _assets_dir_cache
    if _assets_dir_cache is not None:
        return _assets_dir_cache

    candidates = [
        # Development: ai_rom_batch_renamer/modules/ -> project root -> assets/
        Path(__file__).resolve().parent.parent.parent / "assets" / "rom-name-alias-cn",
        # Nuitka onefile: executable sits next to assets/
        Path(sys.executable).parent / "assets" / "rom-name-alias-cn",
        # CWD fallback
        Path(os.getcwd()) / "assets" / "rom-name-alias-cn",
    ]

    for path in candidates:
        if path.is_dir():
            _assets_dir_cache = path
            return path

    return None


# ---------------------------------------------------------------------------
# Helper: strip bracket tags for fuzzy matching
# ---------------------------------------------------------------------------


def _strip_tags(name: str) -> str:
    """Remove (…) […] {…} tags and collapse whitespace."""
    return re.sub(r"\s{2,}", " ", _TAGS_RE.sub("", name)).strip()


def _normalize_cn(name: str) -> str:
    """Normalize a Chinese title for comparison by removing all whitespace.

    This makes "\u8d85\u7ea7\u673a\u5668\u4eba\u5927\u6218A" match "\u8d85\u7ea7\u673a\u5668\u4eba\u5927\u6218 A", etc.
    """
    return re.sub(r"\s+", "", name.lower())


# Roman numeral → Arabic digit conversion for CN key comparison
_ROMAN_RE = re.compile(
    r"(?<![a-zA-Z])(XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)(?![a-zA-Z])",
    re.IGNORECASE,
)
_ROMAN_MAP = {
    "xii": "12",
    "xi": "11",
    "x": "10",
    "ix": "9",
    "viii": "8",
    "vii": "7",
    "vi": "6",
    "v": "5",
    "iv": "4",
    "iii": "3",
    "ii": "2",
    "i": "1",
}


def _normalize_roman(name: str) -> str:
    """Replace standalone Roman numerals with Arabic equivalents.

    e.g. '\u6700\u7ec8\u5e7b\u60f3I, II Advance' \u2192 '\u6700\u7ec8\u5e7b\u60f31, 2 Advance'
    """
    return _ROMAN_RE.sub(lambda m: _ROMAN_MAP.get(m.group(0).lower(), m.group(0)), name)


# Replaces runs of non-CJK, non-digit characters with a single space for _cn_key
_CN_KEY_STRIP_RE = re.compile(r"[^\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af0-9]+")
# Removes spaces at CJK↔digit boundaries (direction-agnostic)
_CN_KEY_CJK_DIGIT_RE = re.compile(r"([\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]) (\d)")
_CN_KEY_DIGIT_CJK_RE = re.compile(r"(\d) ([\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af])")
# Strips CJK blocks — used to extract the non-CJK portion of a mixed title for disambiguation
_NON_CJK_STRIP_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+")


def _cn_key(name: str) -> str:
    """Return a normalized key for CN title comparison.

    Steps:
      1. Convert Roman numerals to Arabic (I→1, II→2, …)
      2. Replace runs of non-CJK/non-digit chars with a single SPACE
         — this preserves the "1 2" vs "12" distinction so that
           '最终幻想 1 + 2' never falsely matches '最终幻想12'.
      3. Remove spaces only at CJK↔digit boundaries.

    Example: '最终幻想I, II Advance' → '最终幻想1 2'
             '最终幻想 1 + 2'        → '最终幻想1 2'   (match ✓)
             '最终幻想XII'           → '最终幻想12'    (no false match ✓)
    """
    keyed = _CN_KEY_STRIP_RE.sub(" ", _normalize_roman(name)).strip()
    keyed = _CN_KEY_CJK_DIGIT_RE.sub(r"\1\2", keyed)
    keyed = _CN_KEY_DIGIT_CJK_RE.sub(r"\1\2", keyed)
    return keyed


# Compiled once at module level – matches digit sequences that are NOT
# immediately preceded or followed by an ASCII letter (i.e. "standalone"
# version numbers such as '3' in '生化危机3', but NOT the '6' in 'X6').
_STANDALONE_DIGIT_RE = re.compile(r"(?<![A-Za-z])\d+(?![A-Za-z])")


def _digits_compatible(query: str, key: str) -> bool:
    """Return True if the *standalone* digit token sets of *query* and *key* are identical.

    Only digits that are NOT immediately preceded or followed by an ASCII letter
    are considered "standalone" version numbers.  This prevents two categories of
    false positives:

    1. Cross-version mismatch:  '生化危机3' must not match '生化危机' (no digits).
    2. Alphanumeric-tag mismatch: '洛克人6' must not match '洛克人X6' because the
       '6' in 'X6' is an alphanumeric suffix, not a standalone version number.

    Examples:
      query '生化危机3' vs key '生化危机'   → {'3'} != {}  → False (correct)
      query '洛克人6'  vs key '洛克人x6'   → {'6'} != {}  → False (correct)
      query '洛克人6'  vs key '洛克人6'    → {'6'} == {'6'} → True  (correct)
      query '洛克人'   vs key '洛克人'     → {}   == {}   → True  (correct)
    """
    return set(_STANDALONE_DIGIT_RE.findall(query)) == set(
        _STANDALONE_DIGIT_RE.findall(key)
    )


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------


def _load_csv(platform: str) -> tuple[CsvIndexes, dict[str, list[dict]]]:
    """Load the CSV for *platform* and return (indexes, fuzzy_index).

    indexes:     CsvIndexes with __exact__, __exact_orig__, __cn_exact__,
                 __cn_fuzzy__, __cn_cjk_key__, __cn_sorted_cjk_key__ keys.
    fuzzy_index: {stripped_name_en_lower: [{"name_en": original, "name_cn": cn}, ...]}
    """
    if platform in _csv_cache:
        return _csv_cache[platform]

    assets_dir = _resolve_assets_dir()
    if assets_dir is None:
        return _EMPTY_INDEXES, {}

    csv_path = assets_dir / f"{platform}.csv"
    if not csv_path.is_file():
        return _EMPTY_INDEXES, {}

    exact: dict[str, str] = {}  # name_en_lower -> name_cn (may be empty str)
    exact_orig: dict[str, str] = {}  # name_en_lower -> original name_en
    fuzzy: dict[str, list[dict]] = {}
    cn_exact: dict[str, dict] = {}  # name_cn_lower -> {name_en, name_cn}
    cn_fuzzy: dict[str, list[dict]] = (
        {}
    )  # stripped_name_cn_lower -> [{name_en, name_cn}, ...]
    cn_cjk_key: dict[str, list[dict]] = (
        {}
    )  # _cn_key(name_cn) -> [{name_en, name_cn}, ...]  (Roman-normalized CJK+digit key)
    cn_sorted_cjk_key: dict[str, list[dict]] = (
        {}
    )  # ""join(sorted(_cn_key(name_cn))) -> entries — order-independent bag-of-chars fallback

    try:
        with open(csv_path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                name_en: str = (row.get("Name EN") or "").strip()
                name_cn: str = (row.get("Name CN") or "").strip()
                if not name_en:
                    continue

                entry = {"name_en": name_en, "name_cn": name_cn}

                key_exact = name_en.lower()
                exact[key_exact] = name_cn
                exact_orig[key_exact] = name_en

                stripped = _strip_tags(name_en).lower()
                fuzzy.setdefault(stripped, []).append(entry)

                # Build reverse CN indexes — prefer US/World region entries
                if name_cn:
                    cn_key_norm_build = _normalize_cn(name_cn)
                    existing = cn_exact.get(cn_key_norm_build)
                    if existing is None or _us_region_score(entry) > _us_region_score(
                        existing
                    ):
                        cn_exact[cn_key_norm_build] = entry
                    stripped_cn = _strip_tags(_normalize_cn(name_cn))
                    cn_fuzzy.setdefault(stripped_cn, []).append(entry)
                    cjk_k = _cn_key(name_cn)
                    if cjk_k:
                        cn_cjk_key.setdefault(cjk_k, []).append(entry)
                        sorted_k = "".join(sorted(cjk_k))
                        if sorted_k != cjk_k:
                            # Only index when char order differs; identical keys are
                            # already covered by cn_cjk_key (Step 3b).
                            cn_sorted_cjk_key.setdefault(sorted_k, []).append(entry)

    except Exception as exc:
        rprint(
            f"[yellow]cn_lookup: 读取 CSV 失败 (Failed to read CSV) {csv_path}: {exc}[/yellow]"
        )
        return _EMPTY_INDEXES, {}

    result: tuple[CsvIndexes, dict[str, list[dict]]] = (
        CsvIndexes(
            __exact__=exact,
            __exact_orig__=exact_orig,
            __cn_exact__=cn_exact,
            __cn_fuzzy__=cn_fuzzy,
            __cn_cjk_key__=cn_cjk_key,
            __cn_sorted_cjk_key__=cn_sorted_cjk_key,
        ),
        fuzzy,
    )
    _csv_cache[platform] = result
    return result


# Regex to detect CJK (Chinese/Japanese/Korean) characters
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def _lookup_csv(base_name: str, platform: str) -> dict | None:
    """Try exact then fuzzy CSV lookup.  Returns {"englishTitle", "chineseTitle"} or None.

    Lookup order:
      1. Exact match against Name EN
      2. Fuzzy match against Name EN (stripped, cutoff 0.85)
      3. If base_name contains CJK chars: exact match against Name CN      3b. CJK+digit key match (Roman->Arabic, strips non-CJK noise)      4. If base_name contains CJK chars: fuzzy match against Name CN (ratio≥85)
      4b. Fallback partial_ratio match against Name CN (partial≥90, handles non-CJK prefix/suffix)
    """
    raw = _load_csv(platform)
    if not raw[0].get("__exact__") and not raw[0].get("__cn_exact__"):
        return None

    exact_meta: CsvIndexes = raw[0]
    fuzzy_index: dict[str, list[dict]] = raw[1]
    exact: dict[str, str] = exact_meta.get("__exact__", {})
    exact_orig: dict[str, str] = exact_meta.get("__exact_orig__", {})
    cn_exact: dict[str, dict] = exact_meta.get("__cn_exact__", {})
    cn_fuzzy: dict[str, list[dict]] = exact_meta.get("__cn_fuzzy__", {})
    cn_cjk_key: dict[str, list[dict]] = exact_meta.get("__cn_cjk_key__", {})
    cn_sorted_cjk_key: dict[str, list[dict]] = exact_meta.get(
        "__cn_sorted_cjk_key__", {}
    )

    # --- Step 1: exact match on Name EN ---
    key = base_name.lower()
    if key in exact:
        cn = exact[key]
        en = exact_orig[key]
        return {"englishTitle": en, "chineseTitle": cn}

    # --- Step 2: fuzzy match on stripped Name EN ---
    stripped_query = _strip_tags(base_name).lower()
    if stripped_query:
        all_stripped_keys = list(fuzzy_index.keys())
        match = fuzz_process.extractOne(
            stripped_query, all_stripped_keys, scorer=fuzz.ratio, score_cutoff=85
        )
        if match:
            best = match[0]
            entries = fuzzy_index[best]
            # Prefer entry with a Chinese title, then US/World region
            cn_entries_only = [e for e in entries if e["name_cn"]]
            pool = cn_entries_only if cn_entries_only else entries
            entry = _prefer_us(pool)
            return {"englishTitle": entry["name_en"], "chineseTitle": entry["name_cn"]}

    # --- Steps 3 & 4: reverse CN lookup (only when input contains CJK characters) ---
    if _CJK_RE.search(base_name):
        # Step 3: exact match on Name CN (space-normalized)
        cn_key_norm = _normalize_cn(base_name)
        if cn_key_norm in cn_exact:
            entry = cn_exact[cn_key_norm]
            return {"englishTitle": entry["name_en"], "chineseTitle": entry["name_cn"]}

        # Step 3b: CJK+digit key match — handles Roman numerals and non-CJK noise
        # e.g. "最终幻想I, II Advance" → "最终幻想1 2" matches CSV "最终幻想 1 + 2"
        cjk_query = _cn_key(base_name)
        if cjk_query and len(cjk_query) >= 2 and cjk_query in cn_cjk_key:
            entries = cn_cjk_key[cjk_query]
            if len(entries) == 1:
                entry = entries[0]
            else:
                # Multiple candidates share the same CJK key — disambiguate by
                # scoring the non-CJK portion of the query against each candidate's
                # name_en and the non-CJK part of name_cn.
                def _norm_nc(s: str) -> str:
                    return (
                        re.sub(r"[-\s]+", " ", _NON_CJK_STRIP_RE.sub("", s))
                        .strip()
                        .lower()
                    )

                non_cjk_q = _norm_nc(base_name)
                if non_cjk_q:

                    def _disambig_score(e: dict) -> int:
                        score_en = fuzz.ratio(
                            non_cjk_q, _strip_tags(e["name_en"]).lower()
                        )
                        cn_nc = _norm_nc(e["name_cn"])
                        score_cn = fuzz.ratio(non_cjk_q, cn_nc) if cn_nc else 0
                        return max(score_en, score_cn)

                    # Use US region score as tiebreaker
                    entry = max(
                        entries, key=lambda e: (_disambig_score(e), _us_region_score(e))
                    )
                else:
                    # Pure CJK input — prefer US/World region entry
                    entry = _prefer_us(entries)
            return {"englishTitle": entry["name_en"], "chineseTitle": entry["name_cn"]}

        # Step 3c: sorted CJK key — handles reordered CJK subtitle segments.
        # e.g. trimmed filename "点点潮流 - 几何世代" (file) vs "几何世代 - 点点潮流" (CSV):
        # same bag of CJK chars, different order → cjk_query sorts equal to CSV key.
        if cjk_query and cn_sorted_cjk_key:
            sorted_cjk_query = "".join(sorted(cjk_query))
            if sorted_cjk_query in cn_sorted_cjk_key:
                entries = cn_sorted_cjk_key[sorted_cjk_query]
                if len(entries) == 1:
                    entry = entries[0]
                else:
                    # Disambiguate by non-CJK portion (same approach as Step 3b)
                    def _norm_nc2(s: str) -> str:
                        return (
                            re.sub(r"[-\s]+", " ", _NON_CJK_STRIP_RE.sub("", s))
                            .strip()
                            .lower()
                        )

                    non_cjk_q2 = _norm_nc2(base_name)
                    if non_cjk_q2:

                        def _disambig_score2(e: dict) -> int:
                            score_en = fuzz.ratio(
                                non_cjk_q2, _strip_tags(e["name_en"]).lower()
                            )
                            cn_nc = _norm_nc2(e["name_cn"])
                            score_cn = fuzz.ratio(non_cjk_q2, cn_nc) if cn_nc else 0
                            return max(score_en, score_cn)

                        # Use US region score as tiebreaker
                        entry = max(
                            entries,
                            key=lambda e: (_disambig_score2(e), _us_region_score(e)),
                        )
                    else:
                        # Pure CJK input — prefer US/World region entry
                        entry = _prefer_us(entries)
                return {
                    "englishTitle": entry["name_en"],
                    "chineseTitle": entry["name_cn"],
                }

        # Step 4: fuzzy match on stripped+normalized Name CN
        stripped_cn_query = _strip_tags(cn_key_norm)
        if stripped_cn_query and cn_fuzzy:
            all_cn_stripped_keys = list(cn_fuzzy.keys())
            # Restrict candidates to digit-compatible keys so that version
            # numbers are respected — e.g. '生化危机3' must not match '生化危机'.
            digit_compat_keys = [
                k
                for k in all_cn_stripped_keys
                if _digits_compatible(stripped_cn_query, k)
            ]
            cn_match = (
                fuzz_process.extractOne(
                    stripped_cn_query,
                    digit_compat_keys,
                    scorer=fuzz.ratio,
                    score_cutoff=85,
                )
                if digit_compat_keys
                else None
            )
            # Step 4b: partial_ratio fallback — handles filenames with non-CJK
            # prefix/suffix (e.g. "Q 棋魂 [简]" → query "q棋魂", key "棋魂").
            # Only consider keys that are at least 2 characters to avoid
            # false positives from very short titles.
            if not cn_match:
                long_keys = [k for k in digit_compat_keys if len(k) >= 2]
                cn_match = (
                    fuzz_process.extractOne(
                        stripped_cn_query,
                        long_keys,
                        scorer=fuzz.partial_ratio,
                        score_cutoff=90,
                    )
                    if long_keys
                    else None
                )
            if cn_match:
                best_cn = cn_match[0]
                cn_entries = cn_fuzzy[best_cn]
                # Prefer entries with an English title, then US/World region
                en_entries_only = [e for e in cn_entries if e["name_en"]]
                pool = en_entries_only if en_entries_only else cn_entries
                entry = _prefer_us(pool)
                return {
                    "englishTitle": entry["name_en"],
                    "chineseTitle": entry["name_cn"],
                }

    return None


# ---------------------------------------------------------------------------
# name_alias(Chinese).json loading
# ---------------------------------------------------------------------------


def _load_name_alias() -> dict:
    """Load and parse name_alias(Chinese).json into a reverse lookup structure.

    Returns a list of records:
      {
        "key": <english IP key, e.g. "Super Mario">,
        "default_cn": <default chinese title>,
        "alias_strings": [list of all aliases (cn + en) for matching],
        "excludes": [list of english substrings that should NOT match],
      }
    """
    global _alias_cache
    if _alias_cache is not None:
        return _alias_cache

    assets_dir = _resolve_assets_dir()
    if assets_dir is None:
        _alias_cache = {}
        return {}

    json_path = assets_dir / "name_alias(Chinese).json"
    if not json_path.is_file():
        _alias_cache = {}
        return {}

    try:
        with open(json_path, encoding="utf-8") as fh:
            raw: dict = json.load(fh)
    except Exception as exc:
        rprint(f"[yellow]cn_lookup: 读取 name_alias JSON 失败: {exc}[/yellow]")
        _alias_cache = {}
        return {}

    records: list[dict] = []
    for key, val in raw.items():
        if not isinstance(val, dict):
            continue
        default_cn: str = str(val.get("default", "")).strip()
        # skip template entries
        if default_cn in ("template", ""):
            continue

        aliases_cn: list[str] = [
            str(a).strip() for a in val.get("alias", []) if str(a).strip()
        ]
        aliases_en: list[str] = [
            str(a).strip() for a in val.get("alias-en", []) if str(a).strip()
        ]
        excludes: list[str] = [
            str(e).strip() for e in val.get("exclude", []) if str(e).strip()
        ]

        # All matchable strings: the key itself + alias-en entries + cn aliases
        alias_strings = [key] + aliases_en + aliases_cn

        records.append(
            {
                "key": key,
                "default_cn": default_cn,
                "alias_strings": alias_strings,
                "aliases_cn": aliases_cn,
                "excludes": excludes,
            }
        )

    _alias_cache = {"records": records}
    return _alias_cache


def _lookup_alias(base_name: str) -> dict | None:
    """Fuzzy match base_name against name_alias entries.

    Strategy:
    - Strip tags from base_name for comparison.
    - For each record, use SequenceMatcher against all alias_strings.
    - Accept if best ratio ≥ 0.80 and base_name doesn't match any exclude string.
    - For Chinese aliases: check if any alias is a substring of base_name (handles
      cases like "超级马里奥 - 失落的时代" containing "超级马里奥").
    """
    data = _load_name_alias()
    records: list[dict] = data.get("records", [])
    if not records:
        return None

    stripped = _strip_tags(base_name).lower()
    base_lower = base_name.lower()

    best_ratio = 0.0
    best_record: dict | None = None

    for record in records:
        # Check excludes: if any exclude substring appears in base_name, skip this record
        excluded = any(excl.lower() in base_lower for excl in record["excludes"])
        if excluded:
            continue

        ratio = 0.0

        # Substring check for Chinese alias strings (handles partial titles)
        for alias in record["aliases_cn"]:
            if alias and alias in base_name:
                ratio = max(ratio, 0.90)  # treat substring match as 90% confidence

        # Fuzzy ratio against all alias strings (stripped)
        for alias_str in record["alias_strings"]:
            if not alias_str:
                continue
            stripped_alias = _strip_tags(alias_str).lower()
            r = fuzz.ratio(stripped, stripped_alias) / 100.0
            ratio = max(ratio, r)

        if ratio >= 0.80 and ratio > best_ratio:
            best_ratio = ratio
            best_record = record

    if best_record is None:
        return None

    return {
        "englishTitle": best_record["key"],
        "chineseTitle": best_record["default_cn"],
    }


# ---------------------------------------------------------------------------
# Helpers: clean display title
# ---------------------------------------------------------------------------


def _clean_english_title(name: str) -> str:
    """Strip region/version tags and collapse whitespace from an English ROM title.

    e.g. "Fire Emblem - Fuuin no Tsurugi (Japan)" → "Fire Emblem - Fuuin no Tsurugi"
    """
    return _strip_tags(name).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def lookup(filename: str, platform: str) -> dict | None:
    """Look up a ROM filename in local alias data.

    Args:
        filename:  The original ROM filename (with or without extension).
        platform:  Canonical platform name (e.g. "Nintendo - Game Boy").

    Returns:
        {"englishTitle": str, "chineseTitle": str} or None if not found.
    """
    # Strip extension to get base name
    base_name, _ = os.path.splitext(filename)

    # Step 1 & 2: CSV lookup (exact then fuzzy) — only when platform has a CSV
    if platform and platform.lower() not in ("", "unknown"):
        result = _lookup_csv(base_name, platform)
        if result and (result["englishTitle"] or result["chineseTitle"]):
            result["englishTitle"] = _clean_english_title(result["englishTitle"])
            return result

    # name_alias(Chinese).json is intentionally NOT used as a fallback here.
    # If the CSV doesn't find a specific ROM entry, return None and let the
    # caller (AI or rename logic) handle the miss.
    return None


def lookupBatch(
    romFiles: list["RomFile"],
    platform: str,
) -> dict[str, dict]:
    """Batch lookup for a list of RomFile objects.

    Returns:
        {originalFilename -> {"englishTitle": str, "chineseTitle": str}}
    """
    results: dict[str, dict] = {}
    hit = 0

    for rf in romFiles:
        # Use rf.fileName (reflects any pre-processing such as trim) so that
        # the lookup operates on the cleaned name; results are still keyed by
        # originalFilename for consistent retrieval in rename.py.
        res = lookup(rf.fileName, platform)
        if res:
            results[rf.originalFilename] = res
            hit += 1

    miss = len(romFiles) - hit
    rprint(
        f"[cyan]中文别名查找 (CN Lookup):[/cyan] 命中 (Hits) [green]{hit}[/green] / "
        f"未找到 (Misses) [yellow]{miss}[/yellow] / 总计 (Total) {len(romFiles)}"
    )
    return results


def get_candidates(filename: str, platform: str, top_n: int = 5) -> list[str]:
    """Return the top-N fuzzy CSV candidate strings for *filename*.

    Each candidate is formatted as ``"English Title (Chinese Title)"`` when a
    Chinese title is available, or just ``"English Title"`` otherwise.
    The richer format gives the AI both the canonical English name and its Chinese
    translation as reference hints.

    Uses ``token_set_ratio`` which is robust to extra tokens such as ``(Japan)``
    and ``(USA)`` commonly found in ROM filenames, and a generous score cutoff of
    40 so that partial or reordered matches still surface as hints.

    Returns an empty list when no CSV is available (e.g. platform unknown).
    """
    if not platform or platform.lower() in ("", "unknown"):
        return []

    raw = _load_csv(platform)
    fuzzy_index: dict[str, list[dict]] = raw[1]
    if not fuzzy_index:
        return []

    base_name, _ = os.path.splitext(filename)
    stripped_query = _strip_tags(base_name).lower()
    if not stripped_query:
        return []

    all_stripped_keys = list(fuzzy_index.keys())
    raw_matches = fuzz_process.extract(
        stripped_query,
        all_stripped_keys,
        # token_set_ratio ignores word order and extra/missing tokens, which is
        # ideal for ROM filenames that append region/version tags.
        scorer=fuzz.token_set_ratio,
        score_cutoff=40,
        limit=top_n,
    )

    candidates: list[str] = []
    seen: set[str] = set()
    for m, _score, _idx in raw_matches:
        entries = fuzzy_index[m]
        for entry in entries[:1]:  # take first entry per fuzzy key
            en = _clean_english_title(entry["name_en"])
            cn = (entry.get("name_cn") or "").strip()
            label = f"{en} ({cn})" if cn else en
            if label not in seen:
                seen.add(label)
                candidates.append(label)

    return candidates[:top_n]
