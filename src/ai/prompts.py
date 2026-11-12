"""System and user prompts designed for ultra-fast Qwen3 8B quiz analysis."""

from src.quiz.models import Question

SYSTEM_PROMPT = """You are an ultra-fast quiz analysis assistant.
Your goal is to provide the correct answer IMMEDIATELY on the first line, followed by confidence and a brief 1-sentence rationale.

Output MUST follow this format:
🎯 ANSWER: [Index] Exact Option Text
⚡ CONFIDENCE: [High/Medium/Low] (Percentage%)
💡 EXPLANATION: [1-2 concise sentences]

Rules:
- Emit the 🎯 ANSWER line first. No greetings, intros, or conversational filler.
- Be decisive and accurate.
"""


def build_question_prompt(question: Question) -> str:
    """Format a standardized Question object into a prompt for the model."""
    return f"""Analyze the question and select the best answer:

{question.format_for_ai()}

Provide the answer immediately in the required format."""
