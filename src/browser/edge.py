"""Microsoft Edge browser implementation using Selenium WebDriver."""

from typing import Optional
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from src.browser.base import BaseBrowser


class EdgeBrowser(BaseBrowser):
    """Microsoft Edge browser implementation."""

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        profile_name: Optional[str] = None,
    ):
        super().__init__(headless=headless, user_data_dir=user_data_dir)
        self.profile_name = profile_name

    def _build_options(self) -> EdgeOptions:
        options = EdgeOptions()
        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            if self.profile_name:
                options.add_argument(f"--profile-directory={self.profile_name}")

        return options

    def launch(self) -> webdriver.Edge:
        """Launch Microsoft Edge with configured options."""
        self.logger.info("Initializing Microsoft Edge...")
        options = self._build_options()
        self.driver = webdriver.Edge(options=options)
        self.logger.info("Microsoft Edge started successfully.")
        return self.driver
