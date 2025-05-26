from sqlite3_cache import Cache


renameHistoryCache = Cache(
    in_memory=False,
    filename="renamerHistory.cache",
)

romInfoCache = Cache(
    in_memory=False,
    filename="renamerRomInfoCache.cache",
)
