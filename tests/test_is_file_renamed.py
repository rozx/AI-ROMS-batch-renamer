import pytest
from ai_rom_batch_renamer.modules import utils as utilsModule

# Test cases cover variations produced by rename logic
@pytest.mark.parametrize("filename,expected", [
    ("星之卡比 (Kirby)(2016)[US].3ds", True),
    ("A 星之卡比 (Kirby: Planet Robobot)(2016)[US][JP].3ds", True),
    ("星之卡比[简].3ds", True),  # Only region added
    ("星之卡比 (Kirby)[简][Hack].3ds", True),
    ("星之卡比 (Kirby)(2016)[简][Hack].3ds", True),
    ("星之卡比 (Kirby)(2016)[简][繁][Hack].3ds", True),
    ("X 星之卡比 (Kirby)(2016)[简].3ds", True),
    ("星之卡比(Kirby)(2016)[US].3ds", True),  # No space before English paren
    ("星之卡比(Kirby)[US].3ds", True),
    ("星之卡比.3ds", False),  # No region marker
    ("Kirby Planet Robobot.3ds", False),  # Not renamed pattern (no region)
    ("星之卡比 (Kirby)2016[US].3ds", False),  # Year not properly parenthesized
    ("A 星之卡比 (Kirby)[US]Extra.3ds", False),  # Extra trailing text
])
def test_is_file_renamed(filename, expected):
    assert utilsModule.isFileRenamed(filename) == expected
