import json
import os
from pathlib import Path


def _default_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "ai-rom-batch-renamer"
        return Path.home() / "AppData" / "Roaming" / "ai-rom-batch-renamer"

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "ai-rom-batch-renamer"
    return Path.home() / ".config" / "ai-rom-batch-renamer"


class AIConfig:
    def __init__(self):
        self.apiKey = ""
        self.model = "deepseek-chat"
        self.endpoint = "https://api.deepseek.com"
        self.v1ChatCompletionsEndpoint = f"{self.endpoint}/chat/completions"
        self.tavilyApiKey = ""
        self.configPath = _default_config_dir() / "config.json"

    def to_dict(self):
        return {
            "apiKey": self.apiKey,
            "model": self.model,
            "endpoint": self.endpoint,
            "tavilyApiKey": self.tavilyApiKey,
        }

    def from_dict(self, data):
        self.apiKey = data.get("apiKey", "")
        self.model = data.get("model", "deepseek-chat")
        self.endpoint = data.get("endpoint", "https://api.deepseek.com")
        self.tavilyApiKey = data.get("tavilyApiKey", "").strip()

    def _read_json_file(self, path: Path):
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load(self):
        legacy_path = Path("config.json")
        try:
            if self.configPath.exists():
                data = self._read_json_file(self.configPath)
                self.from_dict(data)
                return

            if legacy_path.exists():
                data = self._read_json_file(legacy_path)
                self.from_dict(data)
                self.save()
                return

            self.save()
        except FileNotFoundError:
            self.save()
        except Exception as e:
            print(f"Error loading config: {e}")

    def save(self):
        try:
            self.configPath.parent.mkdir(parents=True, exist_ok=True)
            with self.configPath.open("w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f)
        except Exception as e:
            print(f"Error saving config: {e}")
