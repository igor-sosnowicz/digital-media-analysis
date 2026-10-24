"""Project filesystem locations that do not depend on the current working directory."""

from pathlib import Path


def _find_project_root() -> Path:
    """Return the first directory containing both `pyproject.toml` and `config.yaml`.

    The package location is checked before the working directory, so notebooks
    in `notebooks/` and scripts run from the repository root resolve the same paths.
    """
    for start in (Path(__file__).resolve(), Path.cwd().resolve()):
        for directory in (start, *start.parents):
            if (directory / "pyproject.toml").is_file() and (
                directory / "config.yaml"
            ).is_file():
                return directory
    raise FileNotFoundError(
        "Could not locate the project root (a directory with pyproject.toml and config.yaml)."
    )


PROJECT_ROOT = _find_project_root()
DATA_DIR = PROJECT_ROOT / "data"
RAW_REDDIT_DIR = DATA_DIR / "raw" / "reddit"
# Reddit posts of the study period on randomly drawn days: the gold sampling frame.
RAW_REDDIT_FRAME_DIR = DATA_DIR / "raw" / "reddit_frame"
# The drawn sample with the full data of every unit, kept in git so the team shares one copy.
SAMPLES_DIR = PROJECT_ROOT / "data_samples"
RAW_WIKIPEDIA_DIR = DATA_DIR / "raw" / "wikipedia"
CODEBOOK_PATH = PROJECT_ROOT / "codebook" / "codebook.yaml"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
ANNOTATIONS_DIR = PROJECT_ROOT / "annotations"
SHEETS_DIR = ANNOTATIONS_DIR / "sheets"
LABELS_DIR = ANNOTATIONS_DIR / "labels"
AGREEMENT_DIR = ANNOTATIONS_DIR / "agreement"
# Instrument labels for gold units (IDs and labels only) and validation results.
PREDICTIONS_DIR = ANNOTATIONS_DIR / "predictions"
VALIDATION_DIR = ANNOTATIONS_DIR / "validation"
# Raw model output (scores, extracted spans with text), outside git.
MODEL_CACHE_DIR = DATA_DIR / "model_cache"
# Hypothesis tests (docs/hipotezy.md): analysis samples, results, and instrument labels of frame posts.
HYPOTHESES_DIR = ANNOTATIONS_DIR / "hypotheses"
FRAME_LABELS_DIR = ANNOTATIONS_DIR / "frame_labels"
