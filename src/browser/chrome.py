"""Chrome browser implementation using Selenium WebDriver."""

from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from src.browser.base import BaseBrowser


class ChromeBrowser(BaseBrowser):
    """Google Chrome browser implementation."""

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        profile_name: Optional[str] = None,
    ):
        super().__init__(headless=headless, user_data_dir=user_data_dir)
        self.profile_name = profile_name

    def _build_options(self) -> ChromeOptions:
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")

        # Standard stability & anti-detection arguments
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

    def launch(self) -> webdriver.Chrome:
        """Launch Chrome with configured options."""
        self.logger.info("Initializing Google Chrome...")
        options = self._build_options()
        self.driver = webdriver.Chrome(options=options)
        self.logger.info("Google Chrome started successfully.")
        return self.driver
