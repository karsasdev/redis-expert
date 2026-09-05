.PHONY: lint lint-fix

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .
