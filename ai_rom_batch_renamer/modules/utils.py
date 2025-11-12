import datetime
import os
import hashlib
import zipfile
import regex


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


def traversalDirectory(dir: str) -> list[str]:

    fileList: list[str] = []

    if not os.path.isdir(dir):
        return fileList

    for file in os.listdir(dir):

        filePath = os.path.join(dir, file)

        if os.path.isdir(filePath):
            fileList.extend(traversalDirectory(filePath))
        else:
            fileList.append(filePath)

    return fileList


def getBasenameAndExtensions(path: str) -> tuple[str, str]:

    fileName = os.path.basename(path)

    baseName, extension = os.path.splitext(fileName)

    return (baseName, extension)


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

    # 1. Extract contiguous region / hack suffix blocks: [...][...][Hack]
    m_suffix = regex.search(r"(\[[^\]]+\])+\s*$", baseName)
    if not m_suffix:
        return False  # must have at least one region/hack block
    suffix = m_suffix.group(0).strip()
    prefix = baseName[: m_suffix.start()].rstrip()

    # Collect region tokens
    region_tokens = regex.findall(r"\[([^\]]+)\]", suffix)
    if not region_tokens:
        return False
    # Require at least one genuine region (allow Hack optionally)
    if all(t == "Hack" for t in region_tokens):
        return False

    # 2. Optional year in parentheses at end of prefix
    year_match = regex.search(r"\(\d{4}\)$", prefix)
    if year_match:
        prefix = prefix[: year_match.start()].rstrip()
    else:
        # If a naked 4-digit year appears right before regions, disqualify
        if regex.search(r"\d{4}$", prefix):
            return False

    # 3. Optional English title parentheses at end of prefix
    # Examples: (Kirby), (Kirby: Planet Robobot)
    eng_match = regex.search(r"\([^()]+\)$", prefix)
    if eng_match:
        # ensure it has at least one ASCII letter/digit
        inner = eng_match.group(0)
        if regex.search(r"[A-Za-z0-9]", inner):
            prefix = prefix[: eng_match.start()].rstrip()

    # 4. Optional leading pinyin initial: 'X ' or 'A ' etc.
    prefix = regex.sub(r"^[A-Z]\s+", "", prefix)

    # 5. Validate remaining prefix contains at least one CJK or Latin letter
    if not regex.search(r"[\p{Han}A-Za-z]", prefix):
        return False

    # 6. No leftover unmatched brackets or parentheses
    if regex.search(r"[\[\]]", prefix):
        return False
    if prefix.count("(") != prefix.count(")"):
        return False

    return True