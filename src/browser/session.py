"""Automates game code and username entry on Wayground / Quizizz join pages."""

import time
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from src.browser.base import BaseBrowser
from src.utils.logging import get_logger

logger = get_logger("session")


class QuizSessionManager:
    """Handles automated navigation, code submission, and username entry."""

    CODE_SELECTORS = [
        "input[placeholder*='code' i]",
        "input[placeholder*='PIN' i]",
        "input.check-room-input",
        "input[data-testid*='code' i]",
        "input[data-testid*='pin' i]",
        "input[type='tel']",
        "input[aria-label*='code' i]",
        "input[aria-label*='PIN' i]",
        "input[type='text']",
    ]

    NAME_SELECTORS = [
        "input[placeholder*='name' i]",
        "input.enter-name-field",
        "input[data-testid*='name' i]",
        "input[aria-label*='name' i]",
        "input[type='text']",
    ]

    @classmethod
    def _find_first_visible(cls, driver, selectors):
        for sel in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if el.is_displayed() and el.is_enabled():
                        return el
            except Exception:
                continue
        return None

    @classmethod
    def _simulate_typing(cls, driver, element, text: str):
        """Type text and dispatch standard input/change events for React/Vue reactive forms."""
        element.click()
        time.sleep(0.2)
        element.clear()
        element.send_keys(text)

        # Trigger reactive framework input events in case send_keys doesn't fire React's onChange
        trigger_script = """
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """
        try:
            driver.execute_script(trigger_script, element, text)
        except Exception:
            pass

    @classmethod
    def enter_code(cls, browser: BaseBrowser, code: str, timeout: int = 8) -> bool:
        """Locate code input, enter PIN, and submit."""
        if not browser.driver or not code:
            return False

        driver = browser.driver
        logger.info("Looking for game code / PIN input field...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            input_el = cls._find_first_visible(driver, cls.CODE_SELECTORS)
            if input_el:
                print(f"[+] Found code input. Entering game PIN: {code}...")
                cls._simulate_typing(driver, input_el, code)
                time.sleep(0.5)

                # Attempt to find Join button or press ENTER
                try:
                    # Look for Join / Enter button
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    clicked = False
                    for btn in buttons:
                        btn_text = btn.text.strip().lower()
                        if btn.is_displayed() and ("join" in btn_text or "enter" in btn_text or "check" in btn_text):
                            btn.click()
                            clicked = True
                            print("[+] Clicked Join button.")
                            break

                    if not clicked:
                        input_el.send_keys(Keys.ENTER)
                        print("[+] Submitted code via ENTER key.")
                except Exception as exc:
                    logger.debug("Button click error, falling back to ENTER: %s", exc)
                    input_el.send_keys(Keys.ENTER)

                return True

            time.sleep(0.5)

        logger.info("Code input field not detected within %ss (already entered or different screen).", timeout)
        return False

    @classmethod
    def enter_username(cls, browser: BaseBrowser, username: str, timeout: int = 8) -> bool:
        """Locate username input, enter name, and submit."""
        if not browser.driver or not username:
            return False

        driver = browser.driver
        logger.info("Looking for username input field...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            input_el = cls._find_first_visible(driver, cls.NAME_SELECTORS)
            if input_el:
                print(f"[+] Found name input. Entering username: {username}...")
                cls._simulate_typing(driver, input_el, username)
                time.sleep(0.5)

                # Look for Start / Join game button or press ENTER
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    clicked = False
                    for btn in buttons:
                        btn_text = btn.text.strip().lower()
                        if btn.is_displayed() and ("start" in btn_text or "join" in btn_text or "enter" in btn_text):
                            btn.click()
                            clicked = True
                            print("[+] Clicked Start button.")
                            break

                    if not clicked:
                        input_el.send_keys(Keys.ENTER)
                        print("[+] Submitted username via ENTER key.")
                except Exception as exc:
                    logger.debug("Button click error, falling back to ENTER: %s", exc)
                    input_el.send_keys(Keys.ENTER)

                return True

            time.sleep(0.5)

        logger.info("Username input field not detected within %ss.", timeout)
        return False

    @classmethod
    def auto_join(
        cls,
        browser: BaseBrowser,
        code: Optional[str],
        username: Optional[str],
    ) -> None:
        """Perform automated joining flow if code and/or username are supplied."""
        if code:
            cls.enter_code(browser, code, timeout=6)
            time.sleep(2.0)

        if username:
            cls.enter_username(browser, username, timeout=6)
            time.sleep(0.5)
