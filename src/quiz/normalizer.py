"""Normalizes extracted raw quiz data into standard Question and Choice models."""

import html
import re
from typing import List
from src.quiz.models import Choice, Question, QuestionType
from src.quiz.parser import RawExtractedData


class QuestionNormalizer:
    """Cleans, formats, and transforms raw extraction data into standardized Question objects."""

    PREFIX_REGEX = re.compile(r"^(?:[A-Za-z0-9][\.\)\:\-]\s*)+")
    MULTI_SELECT_INDICATORS = [
        "select all that apply",
        "choose all that apply",
        "select all correct",
        "select more than one",
        "all of the following apply",
        "multiple answers",
        "multi-select",
    ]

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Decode HTML entities, remove extra whitespace, and normalize text."""
        if not text:
            return ""
        # Decode entities (&amp;, &quot;, &#39;, etc.)
        decoded = html.unescape(text)
        # Collapse multiple spaces and newlines into single spaces
        normalized = re.sub(r"\s+", " ", decoded).strip()
        return normalized

    @classmethod
    def clean_choice_text(cls, choice_text: str) -> str:
        """Strip redundant list prefixes such as 'A)', '1.', '(a)' from choice text."""
        cleaned = cls.clean_text(choice_text)
        # Remove prefixes like 'A) ' or '1. ' if present
        without_prefix = cls.PREFIX_REGEX.sub("", cleaned).strip()
        return without_prefix if without_prefix else cleaned

    @classmethod
    def detect_question_type(cls, prompt: str, cleaned_choices: List[str]) -> QuestionType:
        """Determine question type from prompt semantics and choice counts."""
        lower_prompt = prompt.lower()

        # Check for multi-select indications in prompt text
        if any(indicator in lower_prompt for indicator in cls.MULTI_SELECT_INDICATORS):
            return QuestionType.MULTI_SELECT

        # Check for True/False
        choice_set = {c.lower() for c in cleaned_choices}
        if choice_set in ({"true", "false"}, {"yes", "no"}):
            return QuestionType.TRUE_FALSE

        # If choices are present
        if len(cleaned_choices) >= 2:
            return QuestionType.MULTIPLE_CHOICE

        if not cleaned_choices:
            return QuestionType.OPEN_ENDED

        return QuestionType.UNKNOWN

    @classmethod
    def normalize(cls, raw: RawExtractedData) -> Question:
        """Convert RawExtractedData into a standardized Question object."""
        cleaned_prompt = cls.clean_text(raw.prompt)

        cleaned_choices: List[Choice] = []
        for idx, raw_choice in enumerate(raw.raw_choices):
            cleaned_str = cls.clean_choice_text(raw_choice)
            if cleaned_str:
                cleaned_choices.append(Choice(text=cleaned_str, index=idx))

        q_type = cls.detect_question_type(
            cleaned_prompt, [c.text for c in cleaned_choices]
        )

        return Question(
            prompt=cleaned_prompt,
            question_type=q_type,
            choices=cleaned_choices,
            image_url=raw.image_url,
            metadata=raw.metadata,
        )
