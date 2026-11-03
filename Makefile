.PHONY: all deps check lint lint-workflows format tests build test-package

all: check

deps:
	uv sync --locked

check: lint tests

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .

lint-workflows:
	actionlint

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

tests:
	uv run --locked --extra images pytest

build:
	rm -rf dist
	uv run --locked python -m build --no-isolation
	uv run --locked twine check --strict dist/*

test-package: build
	set -eu; for distribution in dist/*; do \
		uv run --isolated --no-project --with "$$distribution" python -I -c \
		'import clipboard, importlib.metadata; assert callable(clipboard.copy); assert callable(clipboard.paste); assert callable(clipboard.clear); assert callable(clipboard.set_clipboard_clearer); assert clipboard.VERSION == importlib.metadata.version("clipboard")'; \
	done

