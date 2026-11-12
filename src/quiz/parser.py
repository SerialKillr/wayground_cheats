"""Extracts raw question and options data from the page DOM or raw HTML."""

from dataclasses import dataclass, field
from html.parser import HTMLParser
import re
import time
from typing import Any, Dict, List, Optional
from src.utils.logging import get_logger

logger = get_logger("parser")


@dataclass
class RawExtractedData:
    """Raw unnormalized question information extracted from a page or fixture."""

    prompt: str = ""
    raw_choices: List[str] = field(default_factory=list)
    image_url: Optional[str] = None
    layout: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class _SimpleHTMLTextExtractor(HTMLParser):
    """Utility HTML parser to extract structured question and option chunks."""

    BADGE_TERMS = ("counter", "count", "number", "badge", "index", "indicator", "pill", "timer")

    def __init__(self):
        super().__init__()
        self.in_question = False
        self.option_depth = 0
        self.current_chunk: List[str] = []
        self.prompt_text = ""
        self.options_text: List[str] = []
        self.image_url: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list):
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").lower()
        testid = attr_dict.get("data-testid", "").lower()
        highlight = attr_dict.get("data-highlight-block", "").lower()
        role = attr_dict.get("role", "").lower()

        # Check for image
        if tag == "img" and not self.image_url:
            src = attr_dict.get("src")
            if src and not src.startswith("data:image/svg"):
                self.image_url = src

        # Check for question stem (ignore number badges)
        is_badge = any(b in classes or b in testid for b in self.BADGE_TERMS)
        if not is_badge:
            if (
                highlight == "stem"
                or "question-text" in classes
                or "quiz-question" in classes
                or (("question" in testid or "question" in classes) and "container" not in testid and "container" not in classes)
            ):
                self.in_question = True
                self.current_chunk = []

        # Check for options
        is_container = any(
            c in classes or c in testid
            for c in (
                "options-container",
                "options-grid",
                "options_container",
                "options_grid",
                "optionsgrid",
                "optionscontainer",
                "options-list",
                "choices-container",
                "choices-grid",
                "answers-container",
                "answers-grid",
            )
        )

        if not is_container:
            if self.option_depth > 0:
                self.option_depth += 1
            elif (
                "option" in testid
                or "choice" in testid
                or "answer" in testid
                or "option-card" in classes
                or "choice-card" in classes
                or "answer-option" in classes
                or "option-container" in classes
                or ("option" in classes and "container" not in classes and "grid" not in classes)
                or highlight.startswith("option")
                or role in ("radio", "checkbox")
            ):
                self.option_depth = 1
                self.current_chunk = []

    def handle_data(self, data: str):
        text = data.strip()
        if not text:
            return
        if self.in_question or self.option_depth > 0:
            self.current_chunk.append(text)

    def handle_endtag(self, tag: str):
        if self.in_question and tag in ("div", "p", "span", "h1", "h2", "h3", "section"):
            if self.current_chunk:
                candidate = " ".join(self.current_chunk).strip()
                # Must be a real question sentence, not a single number like "1" or "1 / 10"
                if len(candidate) > 5 and not re.match(r"^\d+(\s*[\/\-]\s*\d+)?$", candidate):
                    if not self.prompt_text or len(candidate) > len(self.prompt_text):
                        self.prompt_text = candidate
            self.in_question = False
            self.current_chunk = []

        if self.option_depth > 0:
            self.option_depth -= 1
            if self.option_depth == 0:
                option_str = " ".join(self.current_chunk).strip()
                if option_str and option_str not in self.options_text and option_str != self.prompt_text:
                    self.options_text.append(option_str)
                self.current_chunk = []


class QuizParser:
    """Parses raw text and structured data from browser DOM or HTML fixtures."""

    EXTRACT_SCRIPT = """
    (function() {
        let prompt = "";
        let promptEl = null;
        let options = [];
        let image = null;

        function isVisible(el) {
            if (!el) return false;
            if (el.offsetWidth > 0 && el.offsetHeight > 0 && el.offsetParent !== null) return true;
            try {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                    return false;
                }
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            } catch(e) {
                return false;
            }
        }

        function cleanText(txt) {
            return (txt || "").replace(/\\s+/g, " ").trim();
        }

        // --- 1. STEM / PROMPT DETECTION ---
        const stemSelectors = [
            "[data-highlight-block='stem']",
            ".question-text-color",
            "[data-testid='question-scroll-container']",
            "[data-testid*='question-text']",
            ".question-text",
            ".quiz-question",
            "[data-testid*='question-container']"
        ];

        const candidatePrompts = [];
        for (const sel of stemSelectors) {
            const els = document.querySelectorAll(sel);
            for (const el of els) {
                if (!isVisible(el)) continue;
                const txt = cleanText(el.innerText || el.textContent);
                // Ignore badges, counters, and tiny texts like "1", "1/10", "1 / 10", "Question 1"
                if (
                    txt.length > 5 &&
                    !/^\\d+(\\s*[\\/\\-]\\s*\\d+)?$/.test(txt) &&
                    !/^(question\\s*\\d+|\\d+\\s*of\\s*\\d+)$/i.test(txt)
                ) {
                    candidatePrompts.push({
                        el: el,
                        text: txt,
                        isSpecific: sel.includes("stem") || sel.includes("text-color") || sel.includes("question-text")
                    });
                }
            }
        }

        // If no stem selector matched, look at .resizeable elements
        if (candidatePrompts.length === 0) {
            const resizables = Array.from(document.querySelectorAll(".resizeable")).filter(isVisible);
            for (const el of resizables) {
                const txt = cleanText(el.innerText || el.textContent);
                if (txt.length > 5 && !/^\\d+(\\s*[\\/\\-]\\s*\\d+)?$/.test(txt)) {
                    const rect = el.getBoundingClientRect();
                    candidatePrompts.push({
                        el: el,
                        text: txt,
                        isSpecific: false,
                        top: rect.top
                    });
                }
            }
            if (candidatePrompts.length > 0) {
                candidatePrompts.sort((a, b) => a.top - b.top);
            }
        }

        if (candidatePrompts.length > 0) {
            const specific = candidatePrompts.filter(c => c.isSpecific);
            if (specific.length > 0) {
                specific.sort((a, b) => b.text.length - a.text.length);
                prompt = specific[0].text;
                promptEl = specific[0].el;
            } else {
                prompt = candidatePrompts[0].text;
                promptEl = candidatePrompts[0].el;
            }
        }

        // --- 2. IMAGE DETECTION ---
        const imgEl = document.querySelector(
            ".question-media img, [data-testid*='question-image'], img[class*='question'], [data-testid='media-image']"
        );
        if (imgEl && imgEl.src && !imgEl.src.startsWith("data:image/svg")) {
            image = imgEl.src;
        }

        // --- 3. OPTIONS / CHOICES DETECTION ---
        function isPartOfPrompt(el) {
            if (!el || !promptEl) return false;
            return el === promptEl || promptEl.contains(el) || el.contains(promptEl);
        }

        function getOptionText(el) {
            if (!el) return "";
            const textChild = el.querySelector(".resizeable, .text-renderer, [class*='text-renderer'], [class*='option-text'], p, span");
            let raw = textChild ? (textChild.innerText || textChild.textContent) : (el.innerText || el.textContent);
            return cleanText(raw);
        }

        const tier1Selectors = [
            "[data-testid^='option-']",
            "[data-testid*='option-card']",
            "[data-testid*='option-container']",
            "[data-testid*='option-trigger']",
            "[data-testid*='choice-']",
            "[data-testid*='answer-']",
            "[data-testid*='game-option']",
            "[data-testid*='option']",
            "[data-highlight-block*='option']",
            "[class*='options-grid'] > *",
            "[class*='optionsGrid'] > *",
            "[class*='options-container'] > *",
            "[class*='optionsContainer'] > *",
            ".options-grid > *",
            ".options-container > *",
            "[class*='option-card']",
            "[class*='choice-card']",
            "[class*='answer-option']",
            "[class*='optionCard']",
            "[class*='choiceCard']",
            ".option-card",
            ".answer-option",
            "[role='radio']",
            "[role='checkbox']"
        ];

        let foundElements = [];
        for (const sel of tier1Selectors) {
            try {
                const matches = Array.from(document.querySelectorAll(sel)).filter(el => {
                    if (!isVisible(el) || isPartOfPrompt(el)) return false;
                    const txt = getOptionText(el);
                    return txt.length > 0 && txt !== prompt;
                });
                if (matches.length >= 2 && matches.length <= 8) {
                    foundElements = matches;
                    break;
                }
            } catch(e) {}
        }

        // Tier 2: Look for .resizeable elements that are NOT the prompt
        if (foundElements.length < 2) {
            const resizeables = Array.from(document.querySelectorAll(".resizeable, [class*='text-renderer']")).filter(el => {
                if (!isVisible(el) || isPartOfPrompt(el)) return false;
                const txt = cleanText(el.innerText || el.textContent);
                return txt.length > 0 && txt !== prompt && !/^\\d+(\\s*[\\/\\-]\\s*\\d+)?$/.test(txt);
            });
            if (resizeables.length >= 2 && resizeables.length <= 8) {
                foundElements = resizeables;
            }
        }

        // Tier 3: All interactive buttons / cards in quiz area
        if (foundElements.length < 2) {
            const allButtons = Array.from(document.querySelectorAll("button, div[role='button'], div[class*='card'], div[class*='option'], div[class*='choice']")).filter(b => {
                if (!isVisible(b) || isPartOfPrompt(b)) return false;
                const rect = b.getBoundingClientRect();
                // Exclude header controls (top 65px) and bottom powerups bar (bottom 50px if height < 55)
                if (rect.top < 65) return false;
                if (rect.bottom > (window.innerHeight - 50) && rect.height < 55) return false;
                if (promptEl) {
                    const pRect = promptEl.getBoundingClientRect();
                    if (rect.top < pRect.top && rect.bottom <= pRect.bottom) return false;
                }
                const txt = getOptionText(b);
                if (!txt || txt === prompt) return false;
                const lower = txt.toLowerCase();
                const controlWords = ["pause", "end", "themes", "settings", "mute", "skip", "edit", "submit", "next", "continue"];
                if (controlWords.some(w => lower === w || lower.startsWith(w + " "))) return false;
                return true;
            });
            if (allButtons.length >= 2 && allButtons.length <= 8) {
                foundElements = allButtons;
            }
        }

        foundElements.forEach(el => {
            const txt = getOptionText(el);
            if (txt && !options.includes(txt) && txt !== prompt) {
                options.push(txt);
            }
        });

        return {
            prompt: prompt,
            options: options,
            image: image
        };
    })();
    """

    @classmethod
    def parse_from_browser(cls, browser: Any) -> Optional[RawExtractedData]:
        """Extract question data from an active Selenium WebDriver instance."""
        if not browser or not browser.is_running:
            return None

        driver = browser.driver

        try:
            # First extraction attempt
            result = driver.execute_script(cls.EXTRACT_SCRIPT)

            # If prompt is found but options haven't rendered yet (due to fade-in animation),
            # wait briefly and retry up to 2.0 seconds.
            if result and result.get("prompt") and len(result.get("options", [])) < 2:
                for _ in range(8):
                    time.sleep(0.25)
                    retry_result = driver.execute_script(cls.EXTRACT_SCRIPT)
                    if retry_result and len(retry_result.get("options", [])) >= 2:
                        result = retry_result
                        break

            # If options are still not found, check HTML page source as well!
            if not result or not result.get("prompt") or len(result.get("options", [])) < 2:
                page_source = browser.get_page_source()
                html_data = cls.parse_from_html(page_source)
                if not result or not result.get("prompt"):
                    return html_data
                if len(result.get("options", [])) < 2 and len(html_data.raw_choices) >= 2:
                    return RawExtractedData(
                        prompt=result.get("prompt", ""),
                        raw_choices=html_data.raw_choices,
                        image_url=result.get("image") or html_data.image_url,
                    )

            return RawExtractedData(
                prompt=result.get("prompt", "") if result else "",
                raw_choices=result.get("options", []) if result else [],
                image_url=result.get("image") if result else None,
            )
        except Exception as exc:
            logger.warning("Browser script extraction failed: %s. Falling back to HTML parse.", exc)
            return cls.parse_from_html(browser.get_page_source())

    @classmethod
    def parse_from_html(cls, html_content: str) -> RawExtractedData:
        """Parse question and options from raw HTML strings without requiring a browser."""
        if not html_content:
            return RawExtractedData()

        extractor = _SimpleHTMLTextExtractor()
        try:
            extractor.feed(html_content)
        except Exception as exc:
            logger.warning("HTML parser error: %s", exc)

        prompt = extractor.prompt_text
        options = list(extractor.options_text)

        # Regex fallback if simple parser did not capture prompt
        if not prompt or len(prompt) <= 5 or re.match(r"^\d+(\s*[\/\-]\s*\d+)?$", prompt):
            m = re.search(
                r"class=['\"][^'\"]*(?:question-text|quiz-question)[^'\"]*['\"][^>]*>([^<]{6,})<",
                html_content,
                re.IGNORECASE,
            )
            if m:
                prompt = m.group(1).strip()

        # Regex fallback for options if empty
        if not options:
            option_matches = re.findall(
                r"(?:data-testid=['\"][^'\"]*(?:option|choice|answer)[^'\"]*['\"]|class=['\"][^'\"]*(?:option-card|choice-card|answer-option|option-container)[^'\"]*['\"])[^>]*>(?:<[^>]+>)*([^<]{1,200})<",
                html_content,
                re.IGNORECASE,
            )
            options = [opt.strip() for opt in option_matches if opt.strip() and opt.strip() != prompt]

        return RawExtractedData(
            prompt=prompt,
            raw_choices=options,
            image_url=extractor.image_url,
        )
