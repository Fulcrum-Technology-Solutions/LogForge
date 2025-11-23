PYTHON ?= python3

.PHONY: install install-dev lint format typecheck test check clean

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check src tests

format:
	black src tests

typecheck:
	mypy src

test:
	pytest

check: format lint typecheck test

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build
