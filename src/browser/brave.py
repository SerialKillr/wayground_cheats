"""Brave browser implementation using Chromium WebDriver."""

import os
import shutil
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from src.browser.base import BaseBrowser


class BraveBrowser(BaseBrowser):
    """Brave browser implementation (Chromium-based)."""

    DEFAULT_WINDOWS_PATHS = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]

    def __init__(
        self,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        profile_name: Optional[str] = None,
        binary_path: Optional[str] = None,
    ):
        super().__init__(headless=headless, user_data_dir=user_data_dir)
        self.profile_name = profile_name
        self.binary_path = binary_path or self._detect_brave_binary()

    def _detect_brave_binary(self) -> Optional[str]:
        """Locate Brave browser binary on the system."""
        # 1. Check PATH
        path_which = shutil.which("brave") or shutil.which("brave-browser")
        if path_which:
            return path_which

        # 2. Check standard Windows installation directories
        for candidate in self.DEFAULT_WINDOWS_PATHS:
            if candidate and os.path.exists(candidate):
                return candidate

        return None

    def _build_options(self) -> ChromeOptions:
        options = ChromeOptions()
        if self.binary_path:
            options.binary_location = self.binary_path
        else:
            self.logger.warning(
                "Brave binary location not automatically found. "
                "Ensure Brave is installed in default directory or PATH."
            )

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

    def launch(self) -> webdriver.Chrome:
        """Launch Brave using Chrome WebDriver with custom binary location."""
        self.logger.info("Initializing Brave Browser...")
        options = self._build_options()
        self.driver = webdriver.Chrome(options=options)
        self.logger.info("Brave Browser started successfully.")
        return self.driver
