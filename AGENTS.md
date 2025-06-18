# AGENTS.md

## General Instructions

* All Python code should strictly follow PEP 8 coding standards.
* Use clear and descriptive naming conventions for variables, functions, and modules.
* Clearly document all public functions and methods with docstrings explaining their purpose and parameters.
* Handle all exceptions gracefully with informative logging.
* Avoid hardcoding values; prefer configurable parameters.

## PR and Commit Instructions

* Pull Request (PR) titles must succinctly reflect the purpose of the changes.
* PR descriptions must clearly outline:

  * The specific changes made
  * The reason or motivation behind these changes
  * Steps taken for testing and validation
* Commit messages should be clear, concise, and informative.

  * Example: "Add scraping functionality for LinkedIn post content"

## File Organization

* Keep scraper scripts under the `src` directory.
* Test scripts must be located within the `tests` directory.

```
project-root/
├── src/
│   └── scraper.py
├── tests/
│   └── test_scraper.py
├── requirements.txt
└── README.md
```

## Validation Checks

Agents must execute these checks after any code changes:

1. Check PEP 8 compliance:

```
flake8 src/ tests/
```

2. Run scraper functionality test:

```
python src/scraper.py --test
```

3. Run unit tests:

```
pytest tests/
```

Ensure all above tests pass before submitting code for review.
