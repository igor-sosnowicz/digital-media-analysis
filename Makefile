.PHONY: pipeline reddit-frame codebook test notebooks gold-sample pilot-round pilot-sheets sample-csv import-labels agreement tune validate import-stance validate-stance label-h1 domain-review hypotheses

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

# Hypotheses (docs/hipotezy.md). Stance sheets: scripts/03b_export_stance_sheets.py; then import them.
import-stance:
	uv run scripts/04b_import_stance_labels.py --phase $(PHASE) $(if $(PARTIAL),--partial)

# Tune on dev (STANCE_TUNE=1), freeze stance_v1, then: make validate-stance SPLIT=test FROZEN=1.
validate-stance:
	uv run --group ml scripts/07b_validate_stance.py --split $(SPLIT) $(if $(STANCE_TUNE),--tune) $(if $(FROZEN),--frozen)

label-h1:
	uv run --group ml scripts/08_label_h1_sample.py

domain-review:
	uv run scripts/08b_export_domain_review.py

# CONFIRMATORY=1 for the reported run, once the preregistration is committed.
hypotheses:
	uv run scripts/09_test_hypotheses.py $(if $(CONFIRMATORY),--confirmatory)

