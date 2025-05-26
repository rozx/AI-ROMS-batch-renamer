import datetime
import os
import hashlib
import zipfile


def isSystemOrHiddenFile(file: str) -> bool:

    baseName = getBasenameAndExtensions(file)[0]
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

    return (
        baseName.startswith(".")
        or baseName.startswith("__")
        or baseName.startswith("~")
        or baseName.startswith("$")
        or baseName.startswith("._")
        or baseName in SYSTEM_OR_IGNORED_FILES
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


def getBasenameAndExtensions(fileName: str) -> tuple[str, str]:

    baseName = os.path.basename(fileName)

    return (
        os.path.splitext(baseName)[0],
        os.path.splitext(baseName)[1],
    )


def getMD5HashFromFile(file: str) -> str:

    with open(file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


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
