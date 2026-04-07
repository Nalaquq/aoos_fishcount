.PHONY: install dev test lint format clean deploy docs

install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest -m "not hardware"

test-all:
	pytest

lint:
	ruff check aoos_fishcount tests scripts
	mypy aoos_fishcount

format:
	black aoos_fishcount tests scripts
	ruff check --fix aoos_fishcount tests scripts

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name ".coverage" -delete
	rm -rf htmlcov dist build *.egg-info

deploy:
	bash scripts/deploy.sh

docs:
	mkdocs serve

health:
	python scripts/health_check.py

focus:
	python scripts/focus_check.py
