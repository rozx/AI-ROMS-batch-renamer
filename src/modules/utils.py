def isSystemOrHiddenFile(file: str) -> bool:

    return (
        file.startswith(".")
        or file.startswith("__")
        or file.startswith("~")
        or file.startswith("$")
        or file == "System Volume Information"
        or file == "RECYCLE.BIN"
        or file == "desktop.ini"
        or file == "Thumbs.db"
        or file == "ehthumbs.db"
        or file == "ehthumbs_vista.db"
        or file == "IconCache.db"
        or file == "ntuser.ini"
        or file == "ntuser.dat"
        or file == "ntuser.dat.log"
        or file == "ntuser.pol"
        or file.startswith("._")
        or file.startswith(".DS_Store")
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
