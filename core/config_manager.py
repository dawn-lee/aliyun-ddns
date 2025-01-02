import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_config()
        return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "access_key_id": "",
            "access_key_secret": "",
            "domain_records": [],
            "check_interval": 300,  # 5分钟检查一次
            "last_ip": "",
        }

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def update_credentials(self, access_key_id: str, access_key_secret: str):
        self.config["access_key_id"] = access_key_id
        self.config["access_key_secret"] = access_key_secret
        self.save_config()