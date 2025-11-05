lint:
	uvx ruff format
	uvx ruff check --fix --unsafe-fixes

type:
	uvx ty check

test:
	uv run pytest -vls
