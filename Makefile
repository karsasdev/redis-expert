.PHONY: lint lint-fix eval

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

eval:
	docker compose exec app uv run python -m scripts.run_eval
