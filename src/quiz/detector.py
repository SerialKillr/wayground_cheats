"""Question detector for identifying quiz interfaces on a web page."""

import re
from typing import Any, List, Optional
from src.utils.logging import get_logger

logger = get_logger("detector")


class QuestionDetector:
    """Detects active quiz questions and options on the current page."""

    # Common DOM selector candidates for question containers and prompts
    QUESTION_SELECTORS = [
        "[data-highlight-block='stem']",
        ".question-text-color",
        "[data-testid='question-scroll-container']",
        "[data-testid*='question-container']",
        "[data-testid*='question-text']",
        "[data-testid*='question']",
        ".question-text",
        ".quiz-question",
        ".current-question",
        ".theme-question-text",
        "div[class*='question-text']",
        "div[class*='questionText']",
        ".resizeable",
    ]

    OPTION_SELECTORS = [
        "[data-testid^='option-trigger']",
        ".options-container",
        ".options-container .option",
        "[data-testid*='option']",
        "[data-testid*='choice']",
        ".option-container",
        ".answer-option",
        "button[class*='option']",
        "div[class*='option-container']",
        "[role='radio']",
        "[role='checkbox']",
    ]

    @classmethod
    def is_question_present(cls, browser: Any) -> bool:
        """Check if an active question element is present on the page via WebDriver."""
        if not browser or not browser.is_running:
            return False

        try:
            # Check via fast JavaScript evaluation
            check_script = """
            (function() {
                function isVisible(el) {
                    if (!el) return false;
                    if (el.offsetWidth > 0 && el.offsetHeight > 0 && el.offsetParent !== null) return true;
                    try {
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    } catch(e) {
                        return false;
                    }
                }

                // 1. Look for question stem
                const stemSelectors = [
                    "[data-highlight-block='stem']",
                    ".question-text-color",
                    ".resizeable",
                    "[data-testid='question-scroll-container']",
                    "[data-testid*='question-text']",
                    ".question-text",
                    ".quiz-question"
                ];
                for (const sel of stemSelectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        if (isVisible(el)) {
                            const txt = (el.innerText || el.textContent || "").trim();
                            // Ignore badge numbers like "1", "1/10", "1 / 10"
                            if (txt.length > 5 && !/^\\d+(\\s*[\\/\\-]\\s*\\d+)?$/.test(txt)) {
                                return true;
                            }
                        }
                    }
                }

                // 2. Look for options presence (at least 2 choices visible)
                const optSelectors = [
                    "[data-testid^='option-']",
                    "[data-testid*='option']",
                    "[data-testid*='choice']",
                    "[data-testid*='answer']",
                    ".options-container > *",
                    ".options-grid > *",
                    "[class*='options-grid'] > *",
                    "[class*='options-container'] > *",
                    "[class*='option-card']",
                    ".option",
                    ".answer-option"
                ];
                for (const sel of optSelectors) {
                    const opts = Array.from(document.querySelectorAll(sel)).filter(
                        o => isVisible(o) && (o.innerText || o.textContent || "").trim().length > 0
                    );
                    if (opts.length >= 2) {
                        return true;
                    }
                }

                return false;
            })();
            """
            result = browser.driver.execute_script(check_script)
            if result:
                return True
        except Exception:
            pass

        # Python fallback via find_elements
        for selector in cls.QUESTION_SELECTORS:
            try:
                elements = browser.find_elements("css selector", selector)
                for elem in elements:
                    if elem.is_displayed():
                        text = elem.text.strip()
                        if len(text) > 5 and not re.match(r"^\d+(\s*[\/\-]\s*\d+)?$", text):
                            return True
            except Exception:
                continue

        return False

    @classmethod
    def is_html_question_present(cls, html_content: str) -> bool:
        """Lightweight regex-based check for question presence in raw HTML strings."""
        patterns = [
            r"data-testid=['\"][^'\"]*question",
            r"class=['\"][^'\"]*question-text",
            r"class=['\"][^'\"]*quiz-question",
            r"class=['\"][^'\"]*option-container",
        ]
        return any(re.search(pat, html_content, re.IGNORECASE) for pat in patterns)
