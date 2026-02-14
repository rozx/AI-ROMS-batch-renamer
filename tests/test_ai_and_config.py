import os
from pathlib import Path

from ai_rom_batch_renamer.modules import ai as aiModule
from ai_rom_batch_renamer.classes.AIConfig import AIConfig


def test_parse_single_pipe_content_with_missing_fields():
    parsed = aiModule._parse_single_pipe_content("Kirby|星之卡比|JP")
    assert parsed is not None
    assert parsed["englishTitle"] == "Kirby"
    assert parsed["chineseTitle"] == "星之卡比"
    assert parsed["region"] == "JP"
    assert parsed["developer"] == ""


def test_parse_single_pipe_content_invalid_text():
    parsed = aiModule._parse_single_pipe_content("not-a-pipe-response")
    assert parsed is None


def test_parse_json_object_with_code_fence():
    text = """```json
{"englishTitle":"Kirby","chineseTitle":"星之卡比","region":"JP","platform":"FC","releaseYear":"1992","publisher":"Nintendo","developer":"HAL"}
```"""
    parsed = aiModule._parse_json_object(text)
    assert parsed is not None
    assert parsed["englishTitle"] == "Kirby"
    assert parsed["chineseTitle"] == "星之卡比"


def test_parse_single_content_prefers_json_object():
    parsed = aiModule._parse_single_content(
        '{"englishTitle":"Contra","chineseTitle":"魂斗罗","region":"US","platform":"NES","releaseYear":"1988","publisher":"Konami","developer":"Konami"}'
    )
    assert parsed is not None
    assert parsed["englishTitle"] == "Contra"
    assert parsed["chineseTitle"] == "魂斗罗"
    assert parsed["releaseYear"] == "1988"


def test_ai_config_save_load_in_user_config_dir(tmp_path, monkeypatch):
    if os.name == "nt":
        monkeypatch.setenv("APPDATA", str(tmp_path))
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    cfg = AIConfig()
    cfg.apiKey = "key-123"
    cfg.model = "deepseek-chat"
    cfg.endpoint = "https://api.deepseek.com"
    cfg.save()

    assert cfg.configPath.exists()

    cfg2 = AIConfig()
    cfg2.load()

    assert cfg2.apiKey == "key-123"
    assert cfg2.model == "deepseek-chat"
    assert cfg2.endpoint == "https://api.deepseek.com"


def test_ai_config_migrate_legacy_config_json(tmp_path, monkeypatch):
    working_dir = tmp_path / "work"
    working_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(working_dir)

    legacy = Path("config.json")
    legacy.write_text('{"apiKey":"legacy-key","model":"m","endpoint":"e"}', encoding="utf-8")

    if os.name == "nt":
        monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    cfg = AIConfig()
    cfg.load()

    assert cfg.apiKey == "legacy-key"
    assert cfg.model == "m"
    assert cfg.endpoint == "e"
    assert cfg.configPath.exists()
