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

The sample holds 500 Reddit posts and 500 Wikipedia edit summaries (pilot, dev and test together), split as evenly as possible across the years of each platform's study period (`study_periods` in `config.yaml`). Each period serves one hypothesis:

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

`scripts/07_kappa_consensus.py` (`make kappa-consensus`) additionally computes Cohen's kappa per annotator pair and variable and writes `annotations/agreement/<phase>_consensus.csv` with the units where both annotators of a pair agreed on a single label.

Both take `PHASE=gold` for the main sample.
