"""Unit tests for Ollama client and prompt construction."""

import json
from unittest.mock import MagicMock, patch
from config.settings import AISettings
from src.ai.ollama import OllamaClient
from src.ai.prompts import SYSTEM_PROMPT, build_question_prompt
from src.quiz.models import Choice, Question, QuestionType


def test_build_question_prompt():
    q = Question(
        prompt="What is the chemical symbol for Gold?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        choices=[Choice("Ag", 0), Choice("Au", 1), Choice("Fe", 2), Choice("Cu", 3)],
    )
    prompt = build_question_prompt(q)

    assert "What is the chemical symbol for Gold?" in prompt
    assert "[1] Au" in prompt
    assert "Provide the answer immediately in the required format." in prompt


def test_ollama_client_unreachable():
    settings = AISettings(host="http://localhost:99999", model="qwen3:8b", think=False)
    client = OllamaClient(settings=settings)
    assert client.is_available() is False


@patch("requests.post")
def test_ollama_streaming_analysis_mock(mock_post):
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response

    mock_lines = [
        json.dumps({"message": {"content": "**Correct Answer:** [1] Au\n"}}).encode("utf-8"),
        json.dumps({"message": {"content": "**Confidence:** High (99%)\n"}}).encode("utf-8"),
        json.dumps({"message": {"content": "**Brief Explanation:** Au is from the Latin aurum.\n"}, "done": True}).encode("utf-8"),
    ]
    mock_response.iter_lines.return_value = iter(mock_lines)
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = OllamaClient()
    question = Question(
        prompt="What is the chemical symbol for Gold?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        choices=[Choice("Ag", 0), Choice("Au", 1)],
    )

    result = client.analyze_question(question)
    assert "[1] Au" in result
    assert "aurum" in result

    # Verify request payload configuration: model, think=False, keep_alive="10m"
    called_payload = mock_post.call_args[1]["json"]
    assert called_payload["model"] == "qwen3:8b"
    assert called_payload["think"] is False
    assert called_payload["keep_alive"] == "30m"
    assert called_payload["options"]["think"] is False
