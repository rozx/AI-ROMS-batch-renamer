import datetime
import os
import hashlib
import zipfile
import regex

from ai_rom_batch_renamer.modules import const as constModule


def isSystemOrHiddenFile(file: str) -> bool:

    baseName = getBasenameAndExtensions(file)[0]
    extension = getBasenameAndExtensions(file)[1]
    fileName = baseName + extension

    SYSTEM_OR_IGNORED_FILES = [
        "System Volume Information",
        "RECYCLE.BIN",
        "desktop.ini",
        "Thumbs.db",
        "ehthumbs.db",
        "ehthumbs_vista.db",
        "IconCache.db",
        "ntuser.ini",
        "ntuser.dat",
        "ntuser.dat.log",
        "ntuser.pol",
        ".DS_Store",
    ]

    IGNORED_FILE_EXTENSIONS = [
        ".bak",
        ".tmp",
        ".log",
        ".old",
        ".swp",
        ".swo",
        ".part",
        ".crdownload",
        ".part",
        ".torrent",
        ".json",
        ".xml",
        ".cache",
        ".db",
        ".sqlite",
        ".sqlite3",
    ]

    currentScript = os.path.basename(__file__)

    # If the file is the same as the current application, then ignore it
    if baseName == os.path.splitext(currentScript)[0]:
        return True

    return (
        baseName.startswith(".")
        or baseName.startswith("__")
        or baseName.startswith("~")
        or baseName.startswith("$")
        or baseName.startswith("._")
        or fileName in SYSTEM_OR_IGNORED_FILES
        or extension in IGNORED_FILE_EXTENSIONS
    )


def getRegion(region: str):

    regionDictList = [
        {
            "item": "US",
            "keys": ["USA", "US", "us", "usa"],
        },
        {
            "item": "JP",
            "keys": ["Japan", "JP", "jp"],
        },
        {
            "item": "EU",
            "keys": ["Europe", "EU", "eu"],
        },
        {
            "item": "繁",
            "keys": ["繁", "繁体", "繁體", "繁中", "TC", "tc"],
        },
        {
            "item": "简",
            "keys": ["简", "简体", "简體", "简中", "中文", "SC", "sc"],
        },
        {
            "item": "简&繁",
            "keys": ["简&繁", "简繁", "繁简", "SC&TC", "sc&tc"],
        },
        {
            "item": "WW",
            "keys": ["World", "WW", "ww"],
        },
        {
            "item": "UE",
            "keys": ["UE", "ue"],
        },
    ]

    return getRegionFromRegionDictList(regionDictList, region)


def getRegionFromRegionDictList(regionList: list[dict], region: str):
    for regionDict in regionList:
        if region in regionDict["keys"]:
            return regionDict["item"]
    return region


def traversalDirectory(directory: str) -> list[str]:

    fileList: list[str] = []

    if not os.path.isdir(directory):
        return fileList

    for file in os.listdir(directory):

        filePath = os.path.join(directory, file)

        if os.path.isdir(filePath):
            fileList.extend(traversalDirectory(filePath))
        else:
            fileList.append(filePath)

    return fileList


def getBasenameAndExtensions(path: str) -> tuple[str, str]:

    fileName = os.path.basename(path)

    baseName, extension = os.path.splitext(fileName)

    return (baseName, extension)


def parseFilesInput(files: str) -> list[str]:
    """Parse GUI/CLI file input string into file paths.

    Supports semicolon and newline separated values.
    """
    if not files:
        return []

    normalized = files.replace("\r\n", "\n").replace("\r", "\n")
    values: list[str] = []

    for line in normalized.split("\n"):
        for part in line.split(";"):
            item = part.strip().strip('"').strip("'")
            if item:
                values.append(item)

    unique_values: list[str] = []
    seen: set[str] = set()
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        unique_values.append(item)

    return unique_values


def getMD5HashFromFile(file: str, chunk_size: int = 1024 * 1024) -> str:
    """Compute an MD5 hash for a file using streaming reads.

    Reading the entire file at once can saturate I/O on slow media (e.g. SD cards).
    Streaming in chunks reduces peak usage and allows the OS to interleave other operations.
    """
    md5 = hashlib.md5()
    try:
        with open(file, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
    except FileNotFoundError:
        return ""
    return md5.hexdigest()


def getTimeStamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def unzipFiles(file, dryrun, passwd) -> list[str]:

    extractedFiles = []
    hadError = False

    with zipfile.ZipFile(file, "r") as zip_ref:
        for extractFile in zip_ref.namelist():

            # decodedFileName = ""

            # try:
            #     decodedFileName = extractFile.encode("cp437").decode("gbk")
            # except:
            #     decodedFileName = extractFile.encode("utf-8").decode("utf-8")

            # targetPath = os.path.join(os.path.dirname(file), decodedFileName)

            try:
                if not dryrun:
                    zip_ref.extract(extractFile, os.path.dirname(file), passwd)

                extractedFiles.append(os.path.join(os.path.dirname(file), extractFile))
            except Exception as e:
                hadError = True
                print(f"Error while unzipping: {e}, Skipping file {file}")

    # finally delete the zip file
    if not dryrun and not hadError:
        os.remove(file)

    return extractedFiles


def isFileRenamed(filePath: str) -> bool:
    baseName, _ = getBasenameAndExtensions(filePath)

    # Primary pattern (Original): one or more region / hack blocks at tail: [...][...][Hack]
    m_suffix = regex.search(r"(\[[^\]]+\])+\s*$", baseName)
    if m_suffix:
        suffix = m_suffix.group(0).strip()
        prefix = baseName[: m_suffix.start()].rstrip()

        region_tokens = regex.findall(r"\[([^\]]+)\]", suffix)
        if not region_tokens:
            return False
        # Require at least one genuine region (not all Hack)
        if all(t == "Hack" for t in region_tokens):
            return False

        # Validate that every region token is among the allowed canonical set.
        # Canonical region codes are those produced by rename logic (getRegion):
        # US, JP, EU, 繁, 简, 简&繁, WW, UE plus special block Hack.
        allowed_regions = constModule.ALLOWED_REGION_CODES
        for t in region_tokens:
            if t == "Hack":
                continue
            if t not in allowed_regions:
                return False

        # Optional year at end of prefix
        year_match = regex.search(r"\(\d{4}\)$", prefix)
        if year_match:
            prefix = prefix[: year_match.start()].rstrip()
        else:
            # Disqualify if naked 4-digit immediately before regions
            if regex.search(r"\d{4}$", prefix):
                return False

        # Optional English title parentheses right before year/regions
        eng_match = regex.search(r"\([^()]+\)$", prefix)
        if eng_match:
            inner = eng_match.group(0)
            if regex.search(r"[A-Za-z0-9]", inner):
                prefix = prefix[: eng_match.start()].rstrip()

        # Optional leading pinyin initial (capital single letter + space)
        prefix = regex.sub(r"^[A-Z]\s+", "", prefix)

        # Validate prefix core content
        if not regex.search(r"[\p{Han}A-Za-z]", prefix):
            return False
        if regex.search(r"[\[\]]", prefix):
            return False
        if prefix.count("(") != prefix.count(")"):
            return False
        return True

    # Secondary pattern (New): ends with a year (YYYY) in parentheses, optionally preceded by an English title in parentheses, but NO region blocks.
    year_tail = regex.search(r"\(\d{4}\)$", baseName)
    if not year_tail:
        return False  # No regions and no year -> not renamed

    prefix = baseName[: year_tail.start()].rstrip()

    # Optional English parentheses right before the year
    eng_match = regex.search(r"\([^()]+\)$", prefix)
    if eng_match:
        inner = eng_match.group(0)
        if regex.search(r"[A-Za-z0-9]", inner):
            prefix = prefix[: eng_match.start()].rstrip()

    # Optional leading pinyin initial
    prefix = regex.sub(r"^[A-Z]\s+", "", prefix)

    # Require at least one Han or Latin letter (Chinese title typically present)
    if not regex.search(r"[\p{Han}A-Za-z]", prefix):
        return False

    # Ensure no stray unmatched brackets; parentheses balance already implicit except English removed
    if regex.search(r"[\[\]]", prefix):
        return False
    if prefix.count("(") != prefix.count(")"):
        return False

    return True


def sanitizePlatform(platform: str) -> str:
    """Map a user-supplied platform alias to the canonical platform name.

    Lookup is case-insensitive.  Empty strings and the sentinel value
    ``"unknown"`` are passed through unchanged.
    Unrecognised values raise ``ValueError`` with a list of close matches.

    Examples
    --------
    >>> sanitizePlatform("gb")
    'Nintendo - Game Boy'
    >>> sanitizePlatform("Game Boy")
    'Nintendo - Game Boy'
    >>> sanitizePlatform("")
    ''
    """
    import difflib

    stripped = platform.strip()
    # Empty / default sentinel – skip validation
    if not stripped or stripped.lower() == "unknown":
        return stripped

    key = stripped.lower()
    canonical = constModule.PLATFORM_ALIASES.get(key)
    if canonical:
        return canonical

    # Build suggestions from all known aliases
    all_keys = list(constModule.PLATFORM_ALIASES.keys())
    close = difflib.get_close_matches(key, all_keys, n=5, cutoff=0.4)
    # Deduplicate while preserving order, show canonical names
    seen: set[str] = set()
    suggestions: list[str] = []
    for k in close:
        c = constModule.PLATFORM_ALIASES[k]
        if c not in seen:
            seen.add(c)
            suggestions.append(c)

    if suggestions:
        hint = "\n  ".join(suggestions)
        raise ValueError(
            f"未知平台 '{stripped}' (Unknown platform).\n"
            f"你是否想输入 (Did you mean):\n  {hint}"
        )
    # No close matches at all – list all canonical names
    all_canonicals = sorted({v for v in constModule.PLATFORM_ALIASES.values()})
    hint = "\n  ".join(all_canonicals)
    raise ValueError(
        f"未知平台 '{stripped}' (Unknown platform).\n"
        f"支持的平台列表 (Supported platforms):\n  {hint}"
    )
