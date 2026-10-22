.PHONY: setup hooks health test structures data data-big validate eval eval-agents analyze ui api

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

raw-pdf:  # raw I(Q) and container files for Open in preprocessing, added to an existing dataset (make data writes them for new samples)
	uv run python -W ignore scripts/make_raw_pdf.py

data-big:  # separate folder, so v1 (dataset/) stays fixed for development and eval
	uv run python -W ignore -m concord.data_builder.build --n 320 --out dataset_big
	uv run python -W ignore scripts/validate_dataset.py --root dataset_big

validate:
	uv run python -W ignore scripts/validate_dataset.py

eval:  # README results table regenerated from results/eval.json; exit status is the evaluation's
	uv run python -W ignore -m concord.evaluate; s=$$?; uv run python scripts/update_readme.py; exit $$s

eval-agents:  # adds visual inspection + generator-critic loop (LLM, ~minutes per sample)
	uv run python -W ignore -m concord.evaluate --agents; s=$$?; uv run python scripts/update_readme.py; exit $$s

analyze:  # make analyze S=dataset/samples/s0010
	uv run python -W ignore -m concord.analysis $(S)

api:  # web API on localhost:8000
	uv run uvicorn backend.app.main:app --port 8000

ui:  # web UI on localhost:3000 (start `make api` first)
	cd web && (test -d node_modules || npm ci) && npm run dev
