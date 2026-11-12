"""Browser abstraction and management package."""

from src.browser.base import BaseBrowser
from src.browser.brave import BraveBrowser
from src.browser.chrome import ChromeBrowser
from src.browser.edge import EdgeBrowser
from src.browser.factory import BrowserFactory
from src.browser.firefox import FirefoxBrowser
from src.browser.session import QuizSessionManager

__all__ = [
    "BaseBrowser",
    "ChromeBrowser",
    "EdgeBrowser",
    "BraveBrowser",
    "FirefoxBrowser",
    "BrowserFactory",
    "QuizSessionManager",
]
