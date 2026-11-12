"""Unit tests for QuizSessionManager automated joining logic."""

from unittest.mock import MagicMock
from src.browser.session import QuizSessionManager


def test_session_manager_enters_code():
    mock_browser = MagicMock()
    mock_driver = MagicMock()
    mock_browser.driver = mock_driver

    # Mock input element
    mock_input = MagicMock()
    mock_input.is_displayed.return_value = True
    mock_input.is_enabled.return_value = True

    # Mock button element
    mock_btn = MagicMock()
    mock_btn.is_displayed.return_value = True
    mock_btn.text = "Join Game"

    mock_driver.find_elements.side_effect = lambda by, sel: (
        [mock_input] if "input" in sel else [mock_btn]
    )

    result = QuizSessionManager.enter_code(mock_browser, "123456", timeout=1)
    assert result is True
    mock_input.clear.assert_called_once()
    mock_input.send_keys.assert_called_with("123456")
    mock_btn.click.assert_called_once()


def test_session_manager_enters_username():
    mock_browser = MagicMock()
    mock_driver = MagicMock()
    mock_browser.driver = mock_driver

    mock_input = MagicMock()
    mock_input.is_displayed.return_value = True
    mock_input.is_enabled.return_value = True

    mock_btn = MagicMock()
    mock_btn.is_displayed.return_value = True
    mock_btn.text = "Start Game"

    mock_driver.find_elements.side_effect = lambda by, sel: (
        [mock_input] if "input" in sel else [mock_btn]
    )

    result = QuizSessionManager.enter_username(mock_browser, "Sriram", timeout=1)
    assert result is True
    mock_input.clear.assert_called_once()
    mock_input.send_keys.assert_called_with("Sriram")
    mock_btn.click.assert_called_once()


def test_session_manager_auto_join_has_delay(monkeypatch):
    from unittest.mock import patch
    mock_browser = MagicMock()
    mock_enter_code = MagicMock()
    mock_enter_name = MagicMock()
    mock_sleep = MagicMock()

    with patch.object(QuizSessionManager, "enter_code", mock_enter_code), \
         patch.object(QuizSessionManager, "enter_username", mock_enter_name), \
         patch("time.sleep", mock_sleep):
        QuizSessionManager.auto_join(mock_browser, "123456", "Sriram")

    mock_enter_code.assert_called_once_with(mock_browser, "123456", timeout=6)
    mock_sleep.assert_any_call(2.0)
    mock_enter_name.assert_called_once_with(mock_browser, "Sriram", timeout=6)
