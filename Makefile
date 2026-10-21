.PHONY: setup hooks health test structures data data-big validate eval ui api

setup: hooks
	uv sync

hooks:
	git config core.hooksPath .githooks

health:
	uv run python -m concord.llm.client

test:
	uv run pytest -q

structures:
	uv run python -W ignore -m concord.data_builder.fetch

data:
	uv run python -W ignore -m concord.data_builder.build --n 60
	uv run python -W ignore scripts/validate_dataset.py

data-big:  # separate folder, so v1 (dataset/) stays fixed for development and eval
	uv run python -W ignore -m concord.data_builder.build --n 320 --out dataset_big
	uv run python -W ignore scripts/validate_dataset.py --root dataset_big

validate:
	uv run python -W ignore scripts/validate_dataset.py
