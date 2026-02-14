import shutil
import tempfile
from pathlib import Path

from sqlite3_cache import Cache

# Use system temp directory for cache files
CACHE_DIR = Path(tempfile.gettempdir()) / "ai-rom-batch-renamer"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

renameHistoryCache = Cache(
    in_memory=False,
    filename="renamerHistory.cache",
    path=str(CACHE_DIR),
)

romInfoCache = Cache(
    in_memory=False,
    filename="renamerRomInfoCache.cache",
    path=str(CACHE_DIR),
)


def clear_all_cache() -> tuple[int, int]:
    """
    Clear all cache files and return the count of cleared items.

    Returns:
        tuple[int, int]: (rom_info_cache_count, rename_history_cache_count)
    """
    # Get counts before clearing
    rom_info_count = len(romInfoCache.get_all_keys())
    rename_history_count = len(renameHistoryCache.get_all_keys())

    # Clear cache data
    romInfoCache.clear()
    renameHistoryCache.clear()

    return rom_info_count, rename_history_count


def delete_cache_files() -> bool:
    """
    Delete the entire cache directory including all cache files.

    Returns:
        bool: True if directory was deleted, False if it didn't exist
    """
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        return True
    return False
