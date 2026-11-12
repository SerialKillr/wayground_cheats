"""Question and Choice standardized data representations."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class QuestionType(str, Enum):
    """Supported question types."""

    MULTIPLE_CHOICE = "multiple_choice"
    MULTI_SELECT = "multi_select"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"
    UNKNOWN = "unknown"


@dataclass
class Choice:
    """Represents a single answer choice."""

    text: str
    index: int
    region: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Choice to dictionary."""
        return asdict(self)


@dataclass
class Question:
    """Standardized representation of an extracted question."""

    prompt: str
    question_type: QuestionType
    choices: List[Choice] = field(default_factory=list)
    image_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def format_for_ai(self) -> str:
        """Format the question into a structured prompt representation for AI analysis."""
        lines = [
            f"Question Type: {self.question_type.value}",
            f"Prompt: {self.prompt.strip()}",
        ]
        if self.image_url:
            lines.append(f"Image Reference: {self.image_url}")

        if self.choices:
            lines.append("Available Options:")
            for choice in self.choices:
                lines.append(f"  [{choice.index}] {choice.text.strip()}")
        else:
            lines.append("No explicit options provided (open-ended).")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Question to dictionary."""
        data = asdict(self)
        data["question_type"] = self.question_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        """Reconstruct Question instance from dictionary."""
        choices_data = data.get("choices", [])
        choices = [
            Choice(
                text=c.get("text", ""),
                index=c.get("index", idx),
                region=c.get("region"),
                metadata=c.get("metadata", {}),
            )
            for idx, c in enumerate(choices_data)
        ]
        q_type_str = data.get("question_type", QuestionType.UNKNOWN.value)
        try:
            q_type = QuestionType(q_type_str)
        except ValueError:
            q_type = QuestionType.UNKNOWN

        return cls(
            prompt=data.get("prompt", ""),
            question_type=q_type,
            choices=choices,
            image_url=data.get("image_url"),
            metadata=data.get("metadata", {}),
        )
