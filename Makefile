.PHONY: pipeline reddit-frame codebook test notebooks gold-sample pilot-round pilot-sheets append-sheets sample-csv import-labels agreement kappa-consensus combine-labels adjudication-sheet import-adjudication tune validate audit-metrics errors compare report-tables preprint-package h2-frame h2-history h1-frame label-h1-v2 h2-links hypotheses-v2 power check-stance import-stance validate-stance label-h1 domain-review hypotheses enriched-stance llm-annotate llm-queue llm-quality

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

# Add the units of a phase that existing workbooks lack, labels kept, e.g. make append-sheets PHASE=pilot ANNOTATORS=IS.
append-sheets:
	uv run scripts/03_export_annotation_sheets.py --phase $(PHASE) --annotators $(ANNOTATORS) --append

# The drawn sample with the full data of every unit, one CSV per platform, into data_samples/.
sample-csv:
	uv run scripts/06_export_sample_csv.py

# PARTIAL=1 when a phase is split between annotators (rows without labels are skipped).
# Rows with invalid labels are left out (listed); workbook problems stop the import.
import-labels:
	uv run scripts/04_import_annotations.py --phase $(PHASE) $(if $(PARTIAL),--partial)

agreement:
	uv run scripts/05_compute_agreement.py --phase $(PHASE)

# Disputed units go to an arbiter (ARBITER=initials); the decisions settle them in the gold reference.
adjudication-sheet:
	uv run scripts/05b_adjudicate.py --phase $(PHASE) --export --arbiter $(ARBITER)

import-adjudication:
	uv run scripts/05b_adjudicate.py --phase $(PHASE) --import

# Cohen's kappa per annotator pair plus consensus cases (single-label agreement).
kappa-consensus:
	uv run scripts/07_kappa_consensus.py --phase $(PHASE)

# Combine both annotators' labels into one dataset per phase.
combine-labels:
	uv run scripts/08_combine_labels.py --phase $(PHASE)

# Instrument validation on gold (needs `uv sync --group ml`). Tune on dev, freeze, then: make validate SPLIT=test FROZEN=1.
# Each instrument runs on test once: name the ones not run yet, e.g. INSTRUMENTS="rules_v2 refs_v1".
SPLIT ?= dev
tune:
	uv run --group ml scripts/07_validate_instruments.py --split dev --tune

validate:
	uv run --group ml scripts/07_validate_instruments.py --split $(SPLIT) $(if $(FROZEN),--frozen) $(if $(INSTRUMENTS),--instruments $(INSTRUMENTS))

# Error rates of gliner_v1 for H1-B from the coded audit workbooks (audit_<annotator>.xlsx).
audit-metrics:
	uv run scripts/07c_audit_metrics.py

# Errors with suggested causes on dev (review in annotations/sheets/errors_dev.xlsx, then IMPORT=1), Pareto chart, differential error.
errors:
	uv run scripts/11_error_analysis.py --split dev $(if $(INSTRUMENTS),--instruments $(INSTRUMENTS)) $(if $(IMPORT),--import)

# Slide 4: kappa of instruments and annotators, McNemar, category rankings; gold shares.
compare:
	uv run scripts/12_compare_instruments.py

# Tables and figures of the LaTeX report (report/raport.tex) from the saved results; compile with pdflatex or Overleaf.
report-tables:
	uv run scripts/13_report_tables.py

# Preprint (v1): number macros report/numbers.tex, compact tables and four figures (docs/preprint_szkic.md).
preprint-package:
	uv run scripts/18_preprint_package.py

# Hypotheses (docs/hipotezy.md). Stance sheets: scripts/03b_export_stance_sheets.py; then import them.
import-stance:
	uv run scripts/04b_import_stance_labels.py --phase $(PHASE) $(if $(PARTIAL),--partial)

# Check filled stance workbooks without writing anything (PARTIAL=1 while coding is under way). Steps: docs/h1a_kroki.md.
check-stance:
	uv run scripts/04b_import_stance_labels.py --phase $(PHASE) --check $(if $(PARTIAL),--partial)

# Tune on dev (STANCE_TUNE=1; STANCE_APPLY=1 writes the best thresholds), commit, then: make validate-stance SPLIT=test FROZEN=1.
validate-stance:
	uv run --group ml scripts/07b_validate_stance.py --split $(SPLIT) $(if $(STANCE_TUNE),--tune) $(if $(STANCE_APPLY),--apply) $(if $(FROZEN),--frozen)

# Plan B, automated annotation (docs/plan_b_automatyzacja.md): enriched stance sample, A1/A2 labels, review queue, quality.
enriched-stance:
	uv run scripts/03e_enriched_stance_sample.py

# e.g. make llm-annotate TASK=stance INPUT=annotations/sheets/llm/stance_gold_JP.xlsx SHEET=Reddit ANNOTATOR=A1
llm-annotate:
	uv run $(if $(filter A1,$(ANNOTATOR)),--with anthropic,--group ml) scripts/19_llm_annotate.py --task $(TASK) --input "$(INPUT)" $(if $(SHEET),--sheet "$(SHEET)") $(if $(KEY),--key $(KEY)) --annotator $(ANNOTATOR) $(if $(ONLY_EMPTY),--only-empty)

llm-queue:
	uv run scripts/20_review_queue.py --task $(TASK) --input "$(INPUT)" $(if $(SHEET),--sheet "$(SHEET)") $(if $(KEY),--key $(KEY)) --a1 "$(A1)" --a2 "$(A2)" --output "$(OUTPUT)" $(if $(ONLY_EMPTY),--only-empty)

llm-quality:
	uv run scripts/21_llm_quality.py --name $(NAME) --task $(TASK) --queue "$(QUEUE)" --reviewed "$(REVIEWED)" $(if $(SHEET),--sheet "$(SHEET)") $(if $(KEY),--key $(KEY))

label-h1:
	uv run --group ml scripts/08_label_h1_sample.py

domain-review:
	uv run scripts/08b_export_domain_review.py

# CONFIRMATORY=1 for the reported run, once the preregistration is committed.
hypotheses:
	uv run scripts/09_test_hypotheses.py $(if $(CONFIRMATORY),--confirmatory)

# Extended tests (docs/hipotezy_v2.md). The downloads need the committed preregistration v2.
h2-frame:
	uv run scripts/00b_resolve_wikipedia_frame.py

h2-history:
	uv run scripts/00c_fetch_wikipedia_history.py $(if $(LIMIT),--limit $(LIMIT))

h1-frame:
	uv run scripts/01c_fetch_h1_topic_frame.py

# ARGS: --validation-annotators IS JP, --import-validation, --tune or --evaluate.
label-h1-v2:
	uv run --group ml scripts/14_label_h1_v2.py $(ARGS)

# ARGS: --fetch-rsp, --resolve-youtube.
h2-links:
	uv run scripts/15_build_h2_links.py $(ARGS)

hypotheses-v2:
	uv run scripts/16_test_hypotheses_v2.py $(if $(CONFIRMATORY),--confirmatory)

power:
	uv run scripts/17_power_analysis.py

