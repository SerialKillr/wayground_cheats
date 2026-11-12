"""Abstract base browser interface defining common WebDriver capabilities."""

from abc import ABC, abstractmethod
import logging
from typing import Any, List, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from src.utils.logging import get_logger


class BaseBrowser(ABC):
    """Abstract browser interface that all browser implementations must follow.

    Ensures consistent lifecycle management (launch, navigate, inspect, quit)
    across Chrome, Edge, Brave, and Firefox.
    """

    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.driver: Optional[WebDriver] = None
        self.logger: logging.Logger = get_logger(self.__class__.__name__)

    @property
    def is_running(self) -> bool:
        """Check if WebDriver is active."""
        return self.driver is not None

    @abstractmethod
    def launch(self) -> WebDriver:
        """Instantiate and start the browser WebDriver."""
        pass

    def open_url(self, url: str) -> None:
        """Navigate to the specified URL."""
        if not self.driver:
            raise RuntimeError("Browser is not running. Call launch() first.")
        self.logger.info("Navigating to: %s", url)
        self.driver.get(url)

    def get_page_source(self) -> str:
        """Return the current page DOM source as an HTML string."""
        if not self.driver:
            raise RuntimeError("Browser is not running.")
        return self.driver.page_source

    def get_current_url(self) -> str:
        """Return the currently open URL."""
        if not self.driver:
            raise RuntimeError("Browser is not running.")
        return self.driver.current_url

    def find_elements(self, by: str, value: str) -> List[WebElement]:
        """Find elements by locator strategy."""
        if not self.driver:
            return []
        return self.driver.find_elements(by, value)

    def find_element(self, by: str, value: str) -> Optional[WebElement]:
        """Find a single element by locator strategy, or None if not found."""
        if not self.driver:
            return None
        elements = self.driver.find_elements(by, value)
        return elements[0] if elements else None

    def execute_script(self, script: str, *args: Any) -> Any:
        """Execute JavaScript synchronously within the browser context."""
        if not self.driver:
            raise RuntimeError("Browser is not running.")
        return self.driver.execute_script(script, *args)

    def quit(self) -> None:
        """Gracefully close and terminate the browser instance."""
        if self.driver:
            self.logger.info("Closing browser session...")
            try:
                self.driver.quit()
            except Exception as exc:
                self.logger.warning("Error during browser quit: %s", exc)
            finally:
                self.driver = None

    def close(self) -> None:
        """Alias for quit."""
        self.quit()

    def __enter__(self) -> "BaseBrowser":
        self.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.quit()
