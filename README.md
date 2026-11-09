# Wayground Cheats

An experimental open-source Python browser automation and AI-assisted quiz analysis project powered by Selenium WebDriver and a locally hosted Ollama language model (Qwen3 8B).

---

## Features

- **Multi-Browser Support**: First-class support for Google Chrome (default), Microsoft Edge, Brave, and Mozilla Firefox via Selenium Manager.
- **Local AI Analysis**: Integrates directly with Ollama running `qwen3:8b`.
  - Thinking mode disabled for near-instant responses.
  - Streaming responses delivered token-by-token directly to your terminal.
  - Model kept alive in memory (`keep_alive="10m"`) to eliminate reload overhead.
  - Model configurations remain internal so users do not have to manage AI parameters.
- **Dynamic DOM Inspection**: Extracts question prompts, multi-layout choices (vertical, horizontal, 2x2 grids), and image references without relying on fragile fixed screen coordinates.
- **Standardized Question Representation**: Normalizes diverse question types (Multiple Choice, Multi-Select, True/False, Open-ended).
- **Educational Scope**: Displays real-time reasoning, confidence ratings, and suggested answers in the terminal without manipulating live assessment inputs or submitting answers automatically.

---

## Architecture & Project Structure

```text
wayground-cheats/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
│
├── main.py                     # Entry point and orchestration loop
│
├── config/
│   └── settings.py             # Internal configuration (Ollama model, timeouts, defaults)
│
├── src/
│   ├── browser/                # Browser automation abstraction
│   │   ├── base.py             # Abstract BaseBrowser interface
│   │   ├── factory.py          # BrowserFactory implementation
│   │   ├── chrome.py           # Google Chrome driver
│   │   ├── edge.py             # Microsoft Edge driver
│   │   ├── brave.py            # Brave browser driver
│   │   └── firefox.py          # Mozilla Firefox driver
│   │
│   ├── quiz/                   # Extraction & representation
│   │   ├── models.py           # Question, Choice, QuestionType dataclasses
│   │   ├── detector.py         # DOM question presence detector
│   │   ├── parser.py           # DOM / HTML text & layout parser
│   │   └── normalizer.py       # Data cleaner & question classifier
│   │
│   ├── ai/                     # Ollama inference
│   │   ├── ollama.py           # Ollama HTTP API client (streaming, keep-alive)
│   │   └── prompts.py          # Optimized Qwen3 8B prompts
│   │
│   ├── cli/                    # User interface
│   │   └── arguments.py        # Terminal argument parser
│   │
│   └── utils/                  # Shared utilities
│       └── logging.py          # Centralized logger
│
└── tests/                      # Independent test suite
    ├── test_quiz_parser.py     # HTML fixture parsing tests
    ├── test_normalizer.py      # Normalization & classification tests
    └── test_ollama.py          # Mock AI API & prompt tests
```

---

## Installation & Setup

### 1. Clone the repository
```powershell
git clone https://github.com/your-username/wayground-cheats.git
cd wayground-cheats
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Setup Ollama and Qwen3 8B
Ensure [Ollama](https://ollama.com/) is installed and running on your system.

```powershell
# Start the Ollama daemon (if not already running)
ollama serve

# Download the Qwen3 8B model
ollama pull qwen3:8b

# Verify installed models
ollama list
```

---

## Usage

Launch the tool by providing session details via command-line arguments.

### Default (Google Chrome)
```powershell
python main.py --code 123456 --username Sriram
```

### Microsoft Edge
```powershell
python main.py --browser edge --code 123456 --username Sriram
```

### Brave Browser
```powershell
python main.py --browser brave --code 123456 --username Sriram
```

### Mozilla Firefox
```powershell
python main.py --browser firefox --code 123456 --username Sriram
```

### Command-Line Arguments

| Flag | Type | Default | Description |
|---|---|---|---|
| `--browser` | string | `chrome` | Browser to use (`chrome`, `edge`, `brave`, `firefox`) |
| `--code` | string | `None` | Game code or session PIN |
| `--username` | string | `None` | Display name for the session |
| `--url` | string | `https://wayground.com/join` | Target URL override |
| `--headless` | flag | `False` | Run browser headlessly without GUI |
| `--debug` | flag | `False` | Enable detailed debug logs |

---

## Running Tests

The test suite runs independently of live browsers or active Ollama servers:

```powershell
python -m pytest tests/ -v
```

---

## Scope Boundary & Disclaimer

This project is created strictly for educational exploration, accessibility analysis, and automated browser testing. It does not manipulate physical input devices, click buttons, or submit answers during live assessments.
