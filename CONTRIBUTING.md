# Contributing

Contributions are welcome. Please open an issue before starting significant work so we can discuss the approach.

## Setting up

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
pytest --cov=bot  # with coverage report
```

All tests must pass before submitting a pull request.

## Linting

```bash
ruff check src tests
```

Fix any errors before submitting. You can run `ruff check --fix src tests` to apply automatic fixes.

## Submitting changes

1. Fork the repository and create a branch from `main`
2. Make your changes
3. Ensure tests pass and linting is clean
4. Open a pull request with a clear description of what changes and why

## Code style

- Line length is 88 characters (enforced by ruff)
- Imports are sorted automatically by ruff
- Python 3.11+ features are fine to use

## Reporting bugs

Open an issue on GitHub with a description of the problem and steps to reproduce it.
