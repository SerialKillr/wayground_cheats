"""AI and Ollama integration package."""

from src.ai.ollama import OllamaClient
from src.ai.prompts import SYSTEM_PROMPT, build_question_prompt

__all__ = ["OllamaClient", "SYSTEM_PROMPT", "build_question_prompt"]
