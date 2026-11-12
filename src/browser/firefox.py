"""Mozilla Firefox browser implementation using Selenium WebDriver."""

from typing import Optional
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from src.browser.base import BaseBrowser


class FirefoxBrowser(BaseBrowser):
    """Mozilla Firefox browser implementation."""

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        profile_name: Optional[str] = None,
    ):
        super().__init__(headless=headless, user_data_dir=user_data_dir)
        self.profile_name = profile_name

    def _build_options(self) -> FirefoxOptions:
        options = FirefoxOptions()
        if self.headless:
            options.add_argument("-headless")

        if self.user_data_dir:
            options.set_preference("profile", self.user_data_dir)

        return options

    def launch(self) -> webdriver.Firefox:
        """Launch Firefox with configured options."""
        self.logger.info("Initializing Mozilla Firefox...")
        options = self._build_options()
        self.driver = webdriver.Firefox(options=options)
        self.logger.info("Mozilla Firefox started successfully.")
        return self.driver
