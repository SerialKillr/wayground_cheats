"""Select model-chosen options in an authorized Wayground test session."""

import re
from typing import Iterable, List
from selenium.webdriver.remote.webelement import WebElement
from src.quiz.models import Question
from src.utils.logging import get_logger

logger = get_logger("selector")


class AnswerSelector:
    """Match normalized option text to visible DOM controls and click them."""

    CANDIDATE_SCRIPT = r"""
    const selectors = [
      "[data-testid^='option-trigger']", "[data-testid*='option-']",
      "[data-testid*='choice']", "[data-highlight-block*='option']",
      ".options-container > *", ".options-grid > *", "[class*='options-grid'] > *",
      "[class*='options-container'] > *", "[class*='optionContainer'] > *",
      ".option", ".answer-option", "[class*='option-card']",
      "[class*='choice-card']", "[role='radio']", "[role='checkbox']"
    ];
    const norm = s => (s || '').replace(/\s+/g, ' ').trim().toLocaleLowerCase();
    const wanted = norm(arguments[0]);
    let all = [];
    for (const selector of selectors) {
      const found = Array.from(document.querySelectorAll(selector)).filter(el => {
        if (!el.getClientRects().length) return false;
        const txt = norm(el.innerText || el.textContent);
        return txt && txt !== norm(arguments[1]);
      });
      if (found.length >= 2) { all = found; break; }
    }
    const exact = all.filter(el => norm(el.innerText || el.textContent) === wanted);
    if (exact.length === 1) {
      let el = exact[0];
      return el.closest("[data-testid^='option-trigger'], [role='radio'], [role='checkbox'], button, [role='button']") || el;
    }
    // Some layouts wrap the visible text in a parent control. Only accept a unique
    // containment match; never guess when two controls could match.
    const partial = all.filter(el => {
      const txt = norm(el.innerText || el.textContent);
      return txt === wanted || (txt.length > wanted.length && txt.includes(wanted));
    });
    if (partial.length === 1) {
      let el = partial[0];
      return el.closest("[data-testid^='option-trigger'], [role='radio'], [role='checkbox'], button, [role='button']") || el;
    }
    return null;
    """

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip().casefold()

    @classmethod
    def select(cls, browser, question: Question, answer_indices: Iterable[int]) -> List[str]:
        """Click only exact, uniquely matched options; raise if any match is ambiguous."""
        if not browser or not browser.driver:
            raise RuntimeError("Browser is not running")
        selected = []
        by_index = {choice.index: choice for choice in question.choices}
        indices = list(dict.fromkeys(answer_indices))
        if not indices:
            raise ValueError("No answer indices were supplied; refusing to guess")

        for index in indices:
            choice = by_index.get(index)
            if choice is None:
                raise ValueError(f"Answer index {index} is not in the extracted choices")
            element = browser.driver.execute_script(
                cls.CANDIDATE_SCRIPT, choice.text, question.prompt
            )
            if element is None:
                raise RuntimeError(f"Could not uniquely locate option: {choice.text!r}")
            if not element.is_displayed() or not element.is_enabled():
                raise RuntimeError(f"Option is not interactable: {choice.text!r}")
            # Avoid toggling an already-selected radio/checkbox option.
            aria_checked = (element.get_attribute("aria-checked") or "").lower()
            aria_pressed = (element.get_attribute("aria-pressed") or "").lower()
            classes = (element.get_attribute("class") or "").lower()
            already_selected = aria_checked == "true" or aria_pressed == "true" or any(
                token in classes.split() for token in ("selected", "is-selected", "active")
            )
            if not already_selected:
                element.click()
            selected.append(choice.text)
            logger.info("Selected option %s: %s", index, choice.text)
        return selected
