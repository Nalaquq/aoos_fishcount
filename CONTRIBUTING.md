# Contributing to aoos_fishcount

Thank you for your interest in contributing. This project supports Tribal fisheries
monitoring capacity in western Alaska.

## Getting Started

1. Fork the repository and clone your fork
2. Create a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
3. Install with dev extras: `pip install -e ".[dev]"`
4. Install pre-commit hooks: `pre-commit install`
5. Create a feature branch: `git checkout -b feature/your-feature`

## Code Standards

- Python 3.11+ with type hints
- Format with `black` (line length 100)
- Lint with `ruff`
- All new functions require docstrings
- All new features require unit tests

## Running Tests

```bash
# Unit tests only (no hardware required)
pytest -m "not hardware"

# All tests (requires RPi + Coral)
pytest
```

## Pull Request Process

1. Ensure all tests pass and linting is clean
2. Update CHANGELOG.md with your changes
3. Update relevant docs if behavior changes
4. Submit PR with a clear description of changes

## Field Data and Privacy

Do not commit real count data, GPS coordinates for active sites,
or subsistence harvest information to this repository.
