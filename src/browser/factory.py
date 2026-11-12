"""Factory for creating browser instances."""

from typing import Any, Dict, List, Type
from src.browser.base import BaseBrowser
from src.browser.brave import BraveBrowser
from src.browser.chrome import ChromeBrowser
from src.browser.edge import EdgeBrowser
from src.browser.firefox import FirefoxBrowser


class BrowserFactory:
    """Factory to instantiate the requested browser implementation."""

    _REGISTRY: Dict[str, Type[BaseBrowser]] = {
        "chrome": ChromeBrowser,
        "edge": EdgeBrowser,
        "brave": BraveBrowser,
        "firefox": FirefoxBrowser,
    }

    @classmethod
    def supported_browsers(cls) -> List[str]:
        """Return list of supported browser identifiers."""
        return list(cls._REGISTRY.keys())

    @classmethod
    def create_browser(cls, browser_name: str, **kwargs: Any) -> BaseBrowser:
        """Instantiate the browser class for the given name.

        Args:
            browser_name: Name of the browser (e.g., 'chrome', 'edge', 'brave', 'firefox')
            **kwargs: Extra arguments passed to the browser constructor (headless, user_data_dir, etc.)

        Returns:
            An instance of BaseBrowser subclass.

        Raises:
            ValueError: If browser_name is not supported.
        """
        key = browser_name.strip().lower()
        browser_cls = cls._REGISTRY.get(key)
        if not browser_cls:
            supported = ", ".join(cls.supported_browsers())
            raise ValueError(
                f"Unsupported browser: '{browser_name}'. Supported browsers are: {supported}"
            )

        return browser_cls(**kwargs)
