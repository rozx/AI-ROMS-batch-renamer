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
    )
