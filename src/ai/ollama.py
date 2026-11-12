"""Ollama API integration for local AI inference with Qwen3 8B."""

import json
from typing import Generator, Optional
import requests
from config.settings import AISettings, SETTINGS
from src.ai.prompts import SYSTEM_PROMPT, build_question_prompt
from src.quiz.models import Question
from src.utils.logging import get_logger

logger = get_logger("ollama")


class OllamaClient:
    """Client for communicating with the local Ollama daemon."""

    def __init__(self, settings: Optional[AISettings] = None):
        self.settings = settings or SETTINGS.ai
        self.base_url = self.settings.host.rstrip("/")

    def is_available(self) -> bool:
        """Check whether the Ollama server is up and reachable."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def is_model_installed(self, model_name: Optional[str] = None) -> bool:
        """Check if the designated model is available locally in Ollama."""
        target = model_name or self.settings.model
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3.0)
            if resp.status_code == 200:
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                # Compare model tags (e.g., 'qwen3:8b' in 'qwen3:8b' or 'qwen3:latest')
                return any(target in m or m.startswith(target.split(":")[0]) for m in models)
        except Exception as exc:
            logger.debug("Failed to list Ollama models: %s", exc)
        return False

    def stream_analysis(self, question: Question) -> Generator[str, None, None]:
        """Stream the AI analysis tokens for the given question.

        Yields:
            Token text chunks as they arrive from Ollama.
        """
        user_prompt = build_question_prompt(question)
        endpoint = f"{self.base_url}/api/chat"

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": True,
            "keep_alive": self.settings.keep_alive,
            "think": self.settings.think,
            "options": {
                "temperature": self.settings.temperature,
                "think": self.settings.think,
                "num_predict": self.settings.num_predict,
                "top_k": 20,
                "top_p": 0.9,
            },
        }

        try:
            with requests.post(
                endpoint,
                json=payload,
                stream=True,
                timeout=self.settings.timeout_seconds,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                yield chunk
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.ConnectionError:
            error_msg = (
                f"\n[ERROR] Unable to connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running (`ollama serve`)."
            )
            logger.error(error_msg)
            yield error_msg
        except requests.exceptions.Timeout:
            error_msg = f"\n[ERROR] Ollama request timed out after {self.settings.timeout_seconds}s."
            logger.error(error_msg)
            yield error_msg
        except Exception as exc:
            error_msg = f"\n[ERROR] Unexpected error querying Ollama: {exc}"
            logger.error(error_msg)
            yield error_msg

    def analyze_question(self, question: Question) -> str:
        """Analyze a question synchronously and return the full text response."""
        chunks = []
        for chunk in self.stream_analysis(question):
            chunks.append(chunk)
        return "".join(chunks)
