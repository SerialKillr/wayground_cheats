"""Application entry point and orchestration for wayground-cheats.

Coordinates browser lifecycle, real-time question detection and extraction,
and live streaming AI analysis via local Ollama (Qwen3 8B).
"""

import hashlib
import sys
import time
from config.settings import SETTINGS
from src.ai.ollama import OllamaClient
from src.browser.factory import BrowserFactory
from src.cli.arguments import parse_arguments
from src.quiz.detector import QuestionDetector
from src.quiz.normalizer import QuestionNormalizer
from src.quiz.parser import QuizParser
from src.utils.logging import get_logger, setup_logging


def get_question_fingerprint(prompt: str) -> str:
    """Generate a unique fingerprint for a question prompt to avoid duplicate analysis."""
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()


def main():
    args = parse_arguments()
    logger = setup_logging(debug=args.debug)

    print("=" * 60)
    print("           WAYGROUND CHEATS — AI QUIZ ASSISTANT            ")
    print("=" * 60)
    print(f"Browser        : {args.browser}")
    print(f"Game Code      : {args.code or 'None (Manual entry in browser)'}")
    print(f"Username       : {args.username or 'None'}")
    print(f"Target URL     : {args.url}")
    print("-" * 60)

    # 1. Initialize AI Client and check status
    ai_client = OllamaClient()
    if ai_client.is_available():
        logger.info("Ollama service is reachable.")
        if ai_client.is_model_installed():
            logger.info("AI Model is ready.")
        else:
            logger.warning(
                "Model '%s' not detected in Ollama. Pull it using: `ollama pull %s`",
                SETTINGS.ai.model,
                SETTINGS.ai.model,
            )
    else:
        logger.warning(
            "Ollama server is not running at %s. Please start it with `ollama serve`.",
            SETTINGS.ai.host,
        )

    # 2. Instantiate and launch browser
    try:
        browser = BrowserFactory.create_browser(
            browser_name=args.browser,
            headless=args.headless,
        )
    except Exception as exc:
        logger.error("Failed to configure browser '%s': %s", args.browser, exc)
        sys.exit(1)

    try:
        browser.launch()
    except Exception as exc:
        logger.error(
            "Failed to launch browser '%s'. Ensure the browser is installed. Error: %s",
            args.browser,
            exc,
        )
        sys.exit(1)

    try:
        # Navigate to target URL
        target_url = args.url
        if args.code and "code=" not in target_url:
            separator = "&" if "?" in target_url else "?"
            target_url = f"{target_url}{separator}pin={args.code}"

        browser.open_url(target_url)
        print("\n[+] Browser session active. Monitoring for questions...")
        print("[!] Note: AI suggestions will appear below automatically.")
        print("[!] Press Ctrl+C in this terminal at any time to quit.\n")

        last_fingerprint = None

        # Continuous detection and analysis loop
        while True:
            try:
                if QuestionDetector.is_question_present(browser):
                    raw_data = QuizParser.parse_from_browser(browser)
                    if raw_data and raw_data.prompt:
                        fingerprint = get_question_fingerprint(raw_data.prompt)

                        # Only analyze if it's a newly detected question
                        if fingerprint != last_fingerprint:
                            last_fingerprint = fingerprint
                            question = QuestionNormalizer.normalize(raw_data)

                            print("\n" + "=" * 60)
                            print(f"[QUESTION DETECTED] ({question.question_type.value.upper()})")
                            print(f"Prompt: {question.prompt}")
                            if question.choices:
                                print("\nChoices:")
                                for choice in question.choices:
                                    print(f"  [{choice.index}] {choice.text}")
                            print("\n--- AI ANALYSIS ---")

                            # Stream Ollama analysis live to terminal
                            for chunk in ai_client.stream_analysis(question):
                                sys.stdout.write(chunk)
                                sys.stdout.flush()
                            print("\n" + "=" * 60 + "\n")

                time.sleep(SETTINGS.browser.poll_interval_seconds)

            except KeyboardInterrupt:
                raise
            except Exception as loop_err:
                logger.debug("Monitoring loop tick error: %s", loop_err)
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n\n[!] Shutdown requested by user. Exiting...")
    finally:
        browser.quit()
        print("[+] Browser session closed. Goodbye!\n")


if __name__ == "__main__":
    main()
