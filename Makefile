.PHONY: pipeline reddit-frame codebook test notebooks gold-sample pilot-sheets sample-csv import-labels agreement

ANNOTATORS ?= A B
PHASE ?= pilot

pipeline:
	uv run scripts/00_fetch_wikipedia_data.py && uv run scripts/01_fetch_reddit_data.py && uv run scripts/01b_fetch_reddit_frame.py

# Reddit posts on random days of the study period (config.yaml), the frame of the gold sample.
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

pilot-sheets:
	uv run scripts/03_export_annotation_sheets.py --phase pilot --annotators $(ANNOTATORS)

# The drawn sample with the full data of every unit, one CSV per platform, into data_samples/.
sample-csv:
	uv run scripts/06_export_sample_csv.py

import-labels:
	uv run scripts/04_import_annotations.py --phase $(PHASE)

agreement:
	uv run scripts/05_compute_agreement.py --phase $(PHASE)
