.PHONY: pipeline reddit-frame codebook test notebooks gold-sample pilot-round pilot-sheets sample-csv import-labels agreement tune validate

ANNOTATORS ?= A B
PHASE ?= pilot

pipeline:
	uv run scripts/00_fetch_wikipedia_data.py && uv run scripts/01_fetch_reddit_data.py && uv run scripts/01b_fetch_reddit_frame.py

# Posts of `reddit_subreddits` on random days (small subreddits: whole years) of the study period (config.yaml), the frame of the gold sample.
reddit-frame:
	uv run scripts/01b_fetch_reddit_frame.py

codebook:
	uv run scripts/render_codebook.py

test:
	uv run pytest

notebooks:
	uv run jupyter nbconvert --to notebook --execute --inplace notebooks/Reditt_EDA.ipynb notebooks/Wikipedia_EDA.ipynb

gold-sample:
	uv run scripts/02_draw_gold_sample.py

# Another pilot round from units outside the sample, e.g. make pilot-round REDDIT=30 WIKIPEDIA=30.
pilot-round:
	uv run scripts/02b_add_pilot_round.py --reddit $(or $(REDDIT),0) --wikipedia $(or $(WIKIPEDIA),0)

pilot-sheets:
	uv run scripts/03_export_annotation_sheets.py --phase pilot --annotators $(ANNOTATORS)

# The drawn sample with the full data of every unit, one CSV per platform, into data_samples/.
sample-csv:
	uv run scripts/06_export_sample_csv.py

# PARTIAL=1 when a phase is split between annotators (rows without labels are skipped).
# DROP_INVALID=1 imports a workbook without its invalid rows (listed) instead of rejecting it.
import-labels:
	uv run scripts/04_import_annotations.py --phase $(PHASE) $(if $(PARTIAL),--partial) $(if $(DROP_INVALID),--drop-invalid)

agreement:
	uv run scripts/05_compute_agreement.py --phase $(PHASE)

# Instrument validation on gold (needs `uv sync --group ml`). Tune on dev, freeze, then: make validate SPLIT=test FROZEN=1.
SPLIT ?= dev
tune:
	uv run --group ml scripts/07_validate_instruments.py --split dev --tune

validate:
	uv run --group ml scripts/07_validate_instruments.py --split $(SPLIT) $(if $(FROZEN),--frozen)

