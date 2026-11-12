"""Command-line interface argument definitions."""

import argparse
from typing import Optional
from config.settings import SETTINGS


def parse_arguments(args: Optional[list] = None) -> argparse.Namespace:
    """Parse and validate command line arguments for the application.

    Note: The AI model is strictly internal configuration and is intentionally
    excluded from user-facing CLI parameters.
    """
    parser = argparse.ArgumentParser(
        prog="wayground-cheats",
        description="AI-assisted quiz analysis and browser automation tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--browser",
        choices=SETTINGS.browser.supported_browsers,
        default=SETTINGS.browser.default_browser,
        help="Target browser to launch (chrome, edge, brave, firefox).",
    )

    parser.add_argument(
        "--code",
        type=str,
        default=None,
        help="Game/Session PIN or joining code.",
    )

    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Display username for the quiz session.",
    )

    parser.add_argument(
        "--url",
        type=str,
        default=SETTINGS.default_url,
        help="Custom target URL to navigate to.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Launch browser in headless mode.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )

    return parser.parse_args(args)
