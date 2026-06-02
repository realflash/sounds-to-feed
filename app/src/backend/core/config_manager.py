import json
import logging
from pathlib import Path

from src.backend.schemas.config import AppConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_path: str = "/config/config.json"):
        self.config_path = Path(config_path)
        self.config = AppConfig()
        self.load_config()

    def load_config(self) -> AppConfig:
        if not self.config_path.exists():
            logger.warning(
                f"Config file not found at {self.config_path}. Using default configuration."
            )
            return self.config

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                self.config = AppConfig(**data)
                logger.info("Successfully loaded configuration")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file: {e}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")

        return self.config

    def get_config(self) -> AppConfig:
        return self.config
