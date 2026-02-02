# Contributing to Swiss Jobs Scraper 🇨🇭

Thank you for your interest in contributing! We welcome efforts to make this tool more robust, extensible, and feature-rich.

## 🛠️ Development Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourrepo/swiss-jobs-scrapper.git
    cd swiss-jobs-scrapper
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    # Install core + dev + all optional extras to ensure full test coverage
    poetry install --all-extras
    poetry shell
    ```

3.  **Install Pre-commit Hooks (Recommended):**
    We use pre-commit to ensure code quality before every commit.
    ```bash
    pip install pre-commit
    pre-commit install
    ```

## 🧪 Running Tests

We prioritize high test coverage and reliability.

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only (fast)
pytest tests/unit/ -v

# Run integration tests (requires docker services if testing DB)
pytest tests/integration/ -v
```

Before submitting a PR, ensure all tests pass and coverage hasn't dropped significantly.

## 🎨 Coding Standards

We use the following tools to maintain code quality:

- **Ruff**: For fast linting.
- **Black**: For uncompromising code formatting.
- **MyPy**: For static type checking (Strict mode).

**Run the full check suite:**
```bash
# Format code
black src/ tests/
isort src/ tests/

# Check linting
ruff check src/

# Check types
mypy src/
```

## 🏗️ Adding a New Provider

To add a new job source (e.g., LinkedIn, Indeed):

1.  Create a new directory in `src/swiss_jobs_scraper/providers/<provider_name>`.
2.  Implement the `BaseJobProvider` abstract base class.
3.  Register your provider in `src/swiss_jobs_scraper/providers/__init__.py`.
4.  Add unit tests in `tests/unit/providers/<provider_name>`.

## 🔄 Pull Request Workflow

1.  Fork the repository.
2.  Create a feature branch: `git checkout -b feat/my-new-feature`.
3.  Commit your changes with descriptive messages.
    - We follow [Conventional Commits](https://www.conventionalcommits.org/).
    - Example: `feat: add support for linkedin scraping`
4.  Push to your fork and submit a Pull Request.
5.  Wait for CI checks to pass and for a reviewer to look at your code.

## 🐛 Bug Reports

Please check existing issues before opening a new one. When reporting a bug, include:
- Command run / API request made.
- Expected vs. actual behavior.
- Logs or error tracebacks.
- Operating system and Python version.

Thank you for helping improve the Swiss Jobs Scraper!
