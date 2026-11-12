"""Unit tests for QuizParser and QuestionDetector on HTML fixtures."""

from src.quiz.detector import QuestionDetector
from src.quiz.parser import QuizParser


def test_parser_extracts_testid_structure():
    html_fixture = """
    <div class="main-container">
        <div data-testid="question-container">
            <h2 data-testid="question-text">What is the speed of light?</h2>
            <img src="https://example.com/physics.jpg" data-testid="question-image" />
        </div>
        <div class="options-grid">
            <button data-testid="option-0">299,792 km/s</button>
            <button data-testid="option-1">150,000 km/s</button>
            <button data-testid="option-2">3,000 km/s</button>
            <button data-testid="option-3">Infinite</button>
        </div>
    </div>
    """
    raw = QuizParser.parse_from_html(html_fixture)
    assert "What is the speed of light?" in raw.prompt
    assert len(raw.raw_choices) == 4
    assert "299,792 km/s" in raw.raw_choices[0]
    assert raw.image_url == "https://example.com/physics.jpg"


def test_parser_extracts_class_based_structure():
    html_fixture = """
    <section>
        <div class="question-text">Which planet is known as the Red Planet?</div>
        <ul>
            <li class="option-container">Mars</li>
            <li class="option-container">Jupiter</li>
            <li class="option-container">Venus</li>
            <li class="option-container">Saturn</li>
        </ul>
    </section>
    """
    raw = QuizParser.parse_from_html(html_fixture)
    assert raw.prompt == "Which planet is known as the Red Planet?"
    assert len(raw.raw_choices) == 4
    assert "Mars" in raw.raw_choices


def test_detector_identifies_question_presence():
    valid_html = """
    <div class="quiz-question">Question text here</div>
    <div class="option-container">Choice 1</div>
    """
    assert QuestionDetector.is_html_question_present(valid_html) is True

    irrelevant_html = """
    <html><body><h1>Welcome to our home page</h1><p>No questions here.</p></body></html>
    """
    assert QuestionDetector.is_html_question_present(irrelevant_html) is False


def test_parser_ignores_counter_badge_and_extracts_math_quiz():
    """Verify that question count pills (e.g. '1 / 10') are ignored in favor of real question stem."""
    wayground_html = """
    <div class="game-view">
        <div class="question-number-pill" data-testid="question-count">
            <span>1</span> / <span>10</span>
        </div>
        <div class="question-text-color resizeable">
            A student is asked to evaluate: (1 + 100) + (2 + 99) + ... + (50 + 51).
        </div>
        <div class="options-grid">
            <div class="option-card" data-testid="option-0">49 pairs each equaling 101</div>
            <div class="option-card" data-testid="option-1">50 pairs each equaling 100</div>
            <div class="option-card" data-testid="option-2">51 pairs each equaling 101</div>
            <div class="option-card" data-testid="option-3">50 pairs each equaling 101</div>
        </div>
    </div>
    """
    raw = QuizParser.parse_from_html(wayground_html)
    assert "A student is asked to evaluate" in raw.prompt
    assert "1 / 10" not in raw.prompt
    assert len(raw.raw_choices) == 4
    assert "50 pairs each equaling 101" in raw.raw_choices[3]


def test_parser_extracts_anatomy_mcq_with_nested_structure():
    """Verify options are extracted even with nested cards, svg icons and resizeable text."""
    anatomy_html = """
    <div class="game-view" style="position: fixed;">
        <div class="question-text-color" data-testid="question-text">
            Movement of the eyeball downward
        </div>
        <div class="options-container" data-testid="options-grid">
            <button class="option-card" data-testid="option-0">
                <svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="5"/></svg>
                <div class="resizeable">
                    <span>Superior oblique</span>
                </div>
            </button>
            <button class="option-card" data-testid="option-1">
                <svg viewBox="0 0 10 10"><rect width="10" height="10"/></svg>
                <div class="resizeable">
                    <span>Inferior rectus</span>
                </div>
            </button>
            <button class="option-card" data-testid="option-2">
                <svg viewBox="0 0 10 10"><polygon points="5,0 10,10 0,10"/></svg>
                <div class="resizeable">
                    <span>Superior rectus</span>
                </div>
            </button>
            <button class="option-card" data-testid="option-3">
                <svg viewBox="0 0 10 10"><polygon points="5,0 10,5 5,10 0,5"/></svg>
                <div class="resizeable">
                    <span>Inferior oblique</span>
                </div>
            </button>
        </div>
    </div>
    """
    raw = QuizParser.parse_from_html(anatomy_html)
    assert raw.prompt == "Movement of the eyeball downward"
    assert len(raw.raw_choices) == 4
    assert "Superior oblique" in raw.raw_choices[0]
    assert "Inferior rectus" in raw.raw_choices[1]
    assert "Superior rectus" in raw.raw_choices[2]
    assert "Inferior oblique" in raw.raw_choices[3]
