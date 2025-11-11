import os
from ai_rom_batch_renamer.modules import rename as renameModule


def test_sanitize_for_os_basic_windows():
    raw = "Dragon's Quest: The Awakening*? <Final>"
    sanitized = renameModule.sanitize_for_os(raw, "windows")
    # Reserved characters removed
    assert "<" not in sanitized and ">" not in sanitized
    assert "*" not in sanitized and "?" not in sanitized
    # Apostrophe retained
    assert "Dragon's" in sanitized
    # Colon removed (not in allowed set)
    assert ":" not in sanitized


def test_get_next_available_name_uniqueness(tmp_path):
    # Simulate existing files
    dir_path = tmp_path
    existing = ["Test.gba", "Test(1).gba"]
    for name in existing:
        (dir_path / name).write_text("dummy")
    result = renameModule.getNextAvailableName("Test.gba", str(dir_path), [], "windows")
    assert result == "Test(2).gba"

