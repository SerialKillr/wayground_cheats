"""Central configuration settings for wayground-cheats.

Contains internal AI model settings, browser defaults, and operational parameters.
"""

from dataclasses import dataclass, field
import os
from typing import List


@dataclass(frozen=True)
class AISettings:
    """Internal AI configuration for Ollama and Qwen3 8B.

    Note: The model name and parameters are internal configurations and
    are not exposed as CLI options to end users.
    """

    host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = "qwen3:8b"
    think: bool = False
    stream: bool = True
    keep_alive: str = "30m"
    temperature: float = 0.0
    num_predict: int = 150
    timeout_seconds: int = 30


@dataclass(frozen=True)
class BrowserSettings:
    """Browser configuration defaults."""

    default_browser: str = "chrome"
    supported_browsers: List[str] = field(
        default_factory=lambda: ["chrome", "edge", "brave", "firefox"]
    )
    implicit_wait_seconds: int = 10
    page_load_timeout_seconds: int = 30
    poll_interval_seconds: float = 1.0


@dataclass(frozen=True)
class AppSettings:
    """Global application settings."""

    app_name: str = "wayground-cheats"
    version: str = "0.1.0"
    default_url: str = "https://wayground.com/join"
    ai: AISettings = field(default_factory=AISettings)
    browser: BrowserSettings = field(default_factory=BrowserSettings)


# Singleton instance for easy import across modules
SETTINGS = AppSettings()
