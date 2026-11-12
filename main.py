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
from src.browser.session import QuizSessionManager
from src.cli.arguments import parse_arguments
from src.quiz.detector import QuestionDetector
from src.quiz.normalizer import QuestionNormalizer
from src.quiz.parser import QuizParser
from src.utils.logging import get_logger, setup_logging


def get_question_fingerprint(prompt: str) -> str:
    """Generate a unique fingerprint for a question prompt to avoid duplicate analysis."""
    return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()


def main():
    if sys.platform == "win32":
        try:
            import os
            os.system("")  # Enable ANSI colors in Windows terminal
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

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

        # Automatically enter game code and username if provided
        if args.code or args.username:
            print("\n[+] Initiating automated session join...")
            QuizSessionManager.auto_join(browser, args.code, args.username)

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
                            question = QuestionNormalizer.normalize(raw_data)
                            last_fingerprint = fingerprint

                            CYAN = "\033[1;36m"
                            YELLOW = "\033[1;33m"
                            WHITE = "\033[1;37m"
                            DIM = "\033[0;90m"
                            RESET = "\033[0m"

                            q_type = question.question_type.value.upper()
                            print(f"\n{CYAN}╔══════════════════════════════════════════════════════════════╗{RESET}")
                            print(f"{CYAN}║ [QUESTION DETECTED] ({q_type}) {RESET}")
                            print(f"{CYAN}╚══════════════════════════════════════════════════════════════╝{RESET}")
                            print(f"{WHITE}{question.prompt}{RESET}\n")

                            if question.choices:
                                print(f"{DIM}Options:{RESET}")
                                for choice in question.choices:
                                    print(f"  {CYAN}[{choice.index}]{RESET} {choice.text}")
                                print()

                            print(f"{YELLOW}--- AI ADVICE ---{RESET}")

                            # Stream Ollama analysis live to terminal
                            for chunk in ai_client.stream_analysis(question):
                                sys.stdout.write(chunk)
                                sys.stdout.flush()

                            print(f"\n{CYAN}{'═' * 64}{RESET}\n")

                time.sleep(SETTINGS.browser.poll_interval_seconds)

            except KeyboardInterrupt:
                raise
            except Exception as loop_err:
                logger.warning("Monitoring loop warning: %s", loop_err)
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n\n[!] Shutdown requested by user. Exiting...")
    finally:
        browser.quit()
        print("[+] Browser session closed. Goodbye!\n")


if __name__ == "__main__":
    main()
