import json


class AIConfig:
    def __init__(self):
        self.apiKey = ""
        self.model = "gpt-4.1"
        self.endpoint = "https://api.openai.com/v1"
        self.v1ChatCompletionsEndpoint = f"{self.endpoint}/chat/completions"

    def to_dict(self):
        return {"apiKey": self.apiKey, "model": self.model, "endpoint": self.endpoint}

    def from_dict(self, data):
        self.apiKey = data.get("apiKey", "")
        self.model = data.get("model", "gpt-4.1")
        self.endpoint = data.get("endpoint", "https://api.openai.com/v1")

    def load(self):
        try:
            with open("config.json", "r") as f:
                data = json.load(f)
                self.from_dict(data)
        except FileNotFoundError:
            self.save()  # Create a new config file if it doesn't exist
            pass

        except Exception as e:
            print(f"Error loading config: {e}")

    def save(self):
        try:
            with open("config.json", "w") as f:
                json.dump(self.to_dict(), f)
        except Exception as e:
            print(f"Error saving config: {e}")
