lint:
	uvx ruff format
	uvx ruff check --fix --unsafe-fixes

type:
	uvx ty check

test:
	uv run pytest -vls

zip-submission:
	@echo "Creating submission zip file..."
	output_file="cs337-nlp-project-2-group-4-part2.zip"; \
	rm "$$output_file" 2>/dev/null || true; \
	zip -r "$$output_file" . \
		-x '*egg-info*' \
		-x '*mypy_cache*' \
		-x '*pytest_cache*' \
		-x '*build*' \
		-x '*ipynb_checkpoints*' \
		-x '*__pycache__*' \
		-x '*.pkl' \
		-x '*.pickle' \
		-x '*.txt' \
		-x '*.log' \
		-x '*.json' \
		-x '*.out' \
		-x '*.err' \
		-x '.git*' \
		-x '.venv/*' \
		-x '.*' \
		-x 'tests/fixtures' \
		-x 'tests/_snapshots' \
		-x '*.pt' \
		-x '*.pth' \
		-x '*.npy' \
		-x '*.npz' ; \
		-x '*examples' ; \
		-x '*.env' ; \
	echo "All files have been compressed into $$output_file"
