# digital-media-analysis

# Setup

0. Ensure you have all pre-requisites installed:
    - [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) – dependency & Python management
    - [make](https://www.gnu.org/software/make/) – meta-build system
    - [git](https://git-scm.com/install/) – version control system

1. Clone the repository.
    
    ```bash
    git clone git@github.com:igor-sosnowicz/digital-media-analysis.git
    ```


2. Install the dependencies.

    ```bash
    uv sync
    ```

3. Run the pipeline.

    ```bash
    make pipeline
    ```

4. Run the tests and re-execute the notebooks.

    ```bash
    make test
    make notebooks
    ```

# Codebook

The annotation codebook lives in `codebook/codebook.yaml`. Version 2.0 uses the nine categories of the "Codebook" slide, with English codes: `scientific`, `institutional`, `media`, `personal`, `social_blog`, `encyclopedia`, `other`, `unknown` and `none` (no source reference). Annotators fill in `source_types` only; `cites_source` is derived from it (0 for `none`, otherwise 1). After editing the codebook, regenerate the annotator guide `codebook/codebook.md`:

```bash
make codebook
```

The frozen baseline instrument is `src/digital_media_analysis/instruments/rules_v1.py`; put rule changes in a new instrument version, not in v1. The validation plan is in `docs/plan_walidacji.md`.

# Gold standard

The sample holds 500 Reddit posts and 500 Wikipedia edit summaries (pilot, dev and test together), plus later pilot rounds drawn from outside it (currently `pilot2`: 30 posts and 30 summaries, so the CSVs hold 530 rows each). The 500 are split as evenly as possible across the years of each platform's study period (`study_periods` in `config.yaml`). Each period serves one hypothesis:

- Reddit, 2005–2020: online trust in the scientific consensus declines. Years get 31 or 32 posts.
- Wikipedia, 2020 to 13 October 2026: users cite alternative sources (blogs, influencers, "independent experts") more often. 2023, 2025 and 2026 are smaller than an even share, so they are taken whole (72, 53 and 59 summaries); the other years get 79.

Each year gives 2 Reddit posts and 3 Wikipedia summaries to the pilot. Every script downloads and samples only the sources `config.yaml` lists: the subreddits of `reddit_subreddits` and the pages of `wikipedia_pages`. For Reddit these are six Polish subreddits (posts from 2012, r/PolskaPolityka from 2020) and r/reddit.com (2005 only, the only source before topical subreddits), r/science (from 2006), r/skeptic and r/conspiracy (from 2008). For each subreddit and year the frame is every post on one random day of each month; a subreddit with fewer than 100 posts on those days is downloaded whole for that year (the Polish subreddits, r/science in 2006, r/skeptic in 2008–2010, r/conspiracy in 2008). `day_weight` (days in the month per drawn day, 1 for a whole year) scales the posts up to their month, and the sample weights include it. Download the frame into `data/raw/reddit_frame/` (separate from the newest posts in `data/raw/reddit/` used by the EDA notebook):

```bash
make reddit-frame
```

The sample is already drawn: `annotations/sample_manifest.csv` lists the units (IDs, year, strata and weights only). Export blind annotation workbooks for the pilot, one per annotator, into `annotations/sheets/` (not tracked by git, since they contain post text):

```bash
make pilot-sheets ANNOTATORS="JP IS"
```

Annotators code the Reddit tab by [`docs/instrukcja_annotacji_reddit.md`](docs/instrukcja_annotacji_reddit.md) and the Wikipedia tab by [`docs/instrukcja_annotacji_wikipedia.md`](docs/instrukcja_annotacji_wikipedia.md): step-by-step guides (in Polish) with the columns to fill, the decision procedure, typical cases and the import error messages.

Write the sample with the full data of every unit to `data_samples/reddit_sample.csv` and `data_samples/wikipedia_sample.csv` (tracked by git, so the team shares one copy). Each file has every column of the raw download, then the sampling columns (`year`, `phase`, `split`, `order`, `stratum`, `signal`, `N_h`, `n_h`, `weight`). The Wikipedia file includes the full article text after each edit (`new_content`, about 51 MB in total); Excel cuts cells longer than 32,767 characters, so read it with pandas:

```bash
make sample-csv
```

Exporting needs the same local data snapshot the sample was drawn from; `annotations/sample_design.json` records its fingerprint, the per-year counts and the years drawn whole. `make gold-sample` redraws the sample and refuses to overwrite an existing manifest unless called with `--force`.

When the filled workbooks are back in `annotations/sheets/` (named `pilot_<annotator>.xlsx`), validate and import them as text-free label files, then compute inter-annotator agreement (Cohen's kappa, Krippendorff's alpha, bootstrap intervals) into `annotations/agreement/`:

```bash
make import-labels
make agreement
```

Both take `PHASE=gold` for the main sample. `DROP_INVALID=1` imports a workbook without its invalid rows (they are listed) instead of rejecting it; header and manifest problems still block.

By default every annotator gets every unit of a phase, as agreement needs. To split the main sample between annotators instead, export only the units after the last row someone already coded and cap how many each platform gets, then import with `PARTIAL=1` (`--partial`), which skips rows without labels and does not require every unit of the phase:

```bash
uv run scripts/03_export_annotation_sheets.py --phase gold --annotators JP --after annotations/sheets/gold_IS.xlsx --reddit 60 --wikipedia 130
make import-labels PHASE=gold PARTIAL=1
```

Agreement is computed only on units at least two people coded, so with a split main sample the pilot is the agreement set.

Another pilot round takes fresh units from the frame that are in none of the earlier splits, so it never touches dev or test. It is appended to the manifest with phase `pilot` and the next split name (`pilot2`, `pilot3`, ...); every pilot workbook then lists the first round, then the next. Re-export the CSVs and the pilot workbooks afterwards:

```bash
make pilot-round REDDIT=30 WIKIPEDIA=30
make sample-csv
```

A workbook someone already started gets the units of the phase it lacks (e.g. the new pilot round) appended below its last row, with the rows and labels already there left as they are. Close the workbook in Excel first:

```bash
make append-sheets PHASE=pilot ANNOTATORS=IS
```

Units that annotators coded differently go to an arbiter. The arbiter workbook (`annotations/sheets/adjudication_<phase>.xlsx`) is not blind: next to the label columns it shows every annotator's labels and notes. The imported decisions (`annotations/adjudication/<phase>.csv`, text-free) settle those units in the gold reference that validation uses:

```bash
make adjudication-sheet PHASE=pilot ARBITER=XY
make import-adjudication PHASE=pilot
```

# Instrument validation

Five instruments label the gold units in codebook space (`cites_source`, `source_types`, `edit_about_sources`), and `scripts/07_validate_instruments.py` compares them with the imported gold labels (and the arbiter's decisions for disputed units):

- `rules_v1`: the frozen keyword and regex extractor from the EDA notebooks (`instruments/rules_v1.py`); it reads only the Reddit post body and does not measure `edit_about_sources`;
- `zeroshot_v1`: a multilingual NLI model ([`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7), MIT) scores one hypothesis per category and one for `edit_about_sources` (`instruments/zeroshot_v1.py`);
- `gliner_v1`: zero-shot entity extraction ([`urchade/gliner_multi-v2.1`](https://huggingface.co/urchade/gliner_multi-v2.1), Apache-2.0) finds source mentions and maps their labels onto the categories (`instruments/gliner_v1.py`);
- `rules_v2`: rules written from the codebook and built on the dev split only (`instruments/rules_v2.py`): whole words, the Reddit post link and its domain (`codebook/domains.yaml` and a list of frequent Reddit domains), Wikipedia shortcuts and reverts left out (R9), the "źródła/przypisy" tag only as `edit_about_sources` (R10), and categories from a name right after a citation cue;
- `refs_v1`: Wikipedia only, `edit_about_sources` = 1 when the edit added or removed at least one reference in the article text (`<ref>` bodies and `{{Cytuj}}` templates) compared with the previous revision (`instruments/refs_v1.py`).

Both models are pinned to a Hugging Face commit and run locally, so no text leaves the machine; a CPU is enough. Install their dependencies with `uv sync --group ml`; the models (about 2.5 GB each) download on first use. The instruments read each unit as the codebook defines it: Reddit title, body and post link (without the author's own image and video hosts, R3), Wikipedia edit summary without the automatic section prefix (R9).

Import the gold labels, tune the model instruments on the dev split, freeze the chosen hypothesis language and thresholds in the instrument modules and commit them, then run the test split once:

```bash
make import-labels PHASE=gold PARTIAL=1 DROP_INVALID=1
make tune
make validate SPLIT=test FROZEN=1
```

The test split refuses to run without `FROZEN=1` or with uncommitted instrument or validation code, and runs once per instrument: an instrument already in `annotations/validation/test_metrics.csv` is refused, so later instruments run alone (`make validate SPLIT=test FROZEN=1 INSTRUMENTS="rules_v2 refs_v1"`), and their rows join the existing tables. Metrics are weighted by the design weights of the coded units in each stratum, with stratified bootstrap intervals: precision, recall, F1 and kappa for `cites_source` and `edit_about_sources`, one-vs-rest F1 for every category (judged only with at least 10 gold positives), and the weighted MASI similarity and macro-F1 for the label set. They are reported per platform, split and annotator. Results go to `annotations/validation/` (metrics, confusion counts, run settings with the commit), instrument labels to `annotations/predictions/`, and raw model output is cached in `data/model_cache/`.

Error analysis and the comparison of instruments use the saved predictions only:

```bash
make errors
make errors IMPORT=1
make compare
```

`make errors` lists every error on the dev split with a cause suggested from a closed list (`annotations/errors/dev_errors.csv`) and writes the review workbook `annotations/sheets/errors_dev.xlsx`, where a person confirms or corrects each cause; `IMPORT=1` reads it back. It also draws the Pareto chart of causes and computes differential error: false positive and false negative rates of `cites_source` by period and by subreddit or page on the test split, with a permutation test. `make compare` writes the kappa of each instrument next to the annotators' kappa in the pilot, exact McNemar tests between instruments, Kendall's tau between category rankings, and the weighted category shares from the gold labels alone (`annotations/validation/gold_shares.csv`).

# Hypotheses

Two research hypotheses are tested on the data, as preregistered in [`docs/hipotezy.md`](docs/hipotezy.md) (settings in the `hypotheses` section of `config.yaml`):

- **H1**, Reddit 2005–2018: online trust in the scientific consensus declines. The primary measure (H1-A) is the share of posts about science that challenge the consensus, from the codebook 2.1 variable `consensus_stance` and the zero-shot instrument `stance_v1`; secondary measures (H1-B) are the shares of citing posts that cite consensus sources (scientific, institutional) or alternative sources (social_blog, unknown, personal), from `gliner_v1`. The posts come from an analysis sample of the frame (at most 150 per subreddit and year) with weights back to the frame.
- **H2**, Wikipedia 2020–2026: users refer more often to alternative sources. The measure is the share of links added to article references whose domain is a blog, social medium or video platform (`codebook/domains.yaml`, `src/digital_media_analysis/wikipedia_refs.py`).

Each trend is the year coefficient of a weighted logistic regression with subreddit or page fixed effects and clustered errors, tested one-sided. Steps:

```bash
uv run scripts/03b_export_stance_sheets.py --phase pilot --splits pilot2 --annotators IS JP
make import-stance PHASE=pilot
make validate-stance SPLIT=dev STANCE_TUNE=1
make validate-stance SPLIT=test FROZEN=1
make label-h1
make domain-review
make hypotheses CONFIRMATORY=1
```

Stance workbooks (`annotations/sheets/stance_<phase>_<annotator>.xlsx`) hold only the Reddit posts and the `consensus_stance` column; gold stance sheets for each annotator's own posts come from `--units-from annotations/sheets/gold_<annotator>.xlsx`. `scripts/08_label_h1_sample.py --audit-annotators ...` also exports audit workbooks for the rare source categories; once they are coded, `make audit-metrics` estimates `gliner_v1`'s sensitivity and specificity for the H1-B indicators (weighted by inverse inclusion probability, also pooled with the gold test split), checks the validity gate and corrects the yearly shares (amendment of 25.10.2026 in the preregistration). The confirmatory run refuses while the preregistration files are uncommitted; H1-A additionally waits for a tuned `stance_v1` that has run on the test split. Results go to `annotations/hypotheses/`.

