"""Unit tests for QuestionNormalizer and Question models."""

from src.quiz.models import Choice, Question, QuestionType
from src.quiz.normalizer import QuestionNormalizer
from src.quiz.parser import RawExtractedData


def test_normalize_multiple_choice():
    raw = RawExtractedData(
        prompt="  What is the capital of France?  ",
        raw_choices=["A) Paris", "B) London", "C) Berlin", "D) Madrid"],
    )
    question = QuestionNormalizer.normalize(raw)

    assert question.prompt == "What is the capital of France?"
    assert question.question_type == QuestionType.MULTIPLE_CHOICE
    assert len(question.choices) == 4
    assert question.choices[0].text == "Paris"
    assert question.choices[0].index == 0
    assert question.choices[1].text == "London"


def test_normalize_true_false():
    raw = RawExtractedData(
        prompt="The Earth is flat.",
        raw_choices=["True", "False"],
    )
    question = QuestionNormalizer.normalize(raw)

    assert question.prompt == "The Earth is flat."
    assert question.question_type == QuestionType.TRUE_FALSE
    assert len(question.choices) == 2


def test_normalize_multi_select():
    raw = RawExtractedData(
        prompt="Which of the following are prime numbers? Select all that apply.",
        raw_choices=["2", "3", "4", "5"],
    )
    question = QuestionNormalizer.normalize(raw)

    assert question.question_type == QuestionType.MULTI_SELECT
    assert len(question.choices) == 4


def test_clean_text_html_entities():
    raw = RawExtractedData(
        prompt="Which symbol represents &quot;greater than&quot; &amp; &lt;less than&gt;?",
        raw_choices=["&gt; and &lt;", "== and !="],
    )
    question = QuestionNormalizer.normalize(raw)

    assert 'Which symbol represents "greater than" & <less than>?' == question.prompt
    assert question.choices[0].text == "> and <"


def test_question_serialization():
    question = Question(
        prompt="Sample prompt",
        question_type=QuestionType.MULTIPLE_CHOICE,
        choices=[Choice(text="Option A", index=0), Choice(text="Option B", index=1)],
        image_url="https://example.com/image.png",
    )

    data = question.to_dict()
    assert data["question_type"] == "multiple_choice"
    assert len(data["choices"]) == 2

    restored = Question.from_dict(data)
    assert restored.prompt == question.prompt
    assert restored.question_type == QuestionType.MULTIPLE_CHOICE
    assert restored.choices[0].text == "Option A"
    assert restored.image_url == "https://example.com/image.png"


def test_format_for_ai():
    question = Question(
        prompt="What is 2 + 2?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        choices=[Choice(text="3", index=0), Choice(text="4", index=1)],
    )
    prompt_str = question.format_for_ai()
    assert "Question Type: multiple_choice" in prompt_str
    assert "Prompt: What is 2 + 2?" in prompt_str
    assert "[0] 3" in prompt_str
    assert "[1] 4" in prompt_str
