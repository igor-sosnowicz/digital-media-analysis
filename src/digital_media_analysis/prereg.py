"""Guards of the preregistrations: the files each one freezes and a check that they are committed.

v2 (docs/hipotezy_v2.md) freezes its document, the configuration, the topic
and owner lists and the analysis code before any v2 data is downloaded, so
the download scripts refuse to run while those files differ from HEAD.
"""

import subprocess

from digital_media_analysis.paths import PROJECT_ROOT

PREREGISTRATION_V2 = [
    "docs/hipotezy_v2.md", "config.yaml", "codebook/topics.yaml", "codebook/owners.yaml",
    "src/digital_media_analysis/inference.py", "src/digital_media_analysis/h1_frame.py",
    "src/digital_media_analysis/wikipedia_frame.py", "src/digital_media_analysis/wikipedia_history.py",
    "src/digital_media_analysis/owners.py", "src/digital_media_analysis/topics.py",
    "scripts/16_test_hypotheses_v2.py",
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def uncommitted(paths: list[str] = PREREGISTRATION_V2) -> str:
    """`git status --porcelain` lines of the given files that differ from HEAD ('' when all are committed)."""
    return git("status", "--porcelain", "--", *paths)


def require_committed(paths: list[str] = PREREGISTRATION_V2) -> str:
    """The HEAD commit; exits with the list of files when the preregistration is not committed."""
    if dirty := uncommitted(paths):
        raise SystemExit(f"Commit the preregistration v2 first (docs/hipotezy_v2.md); uncommitted:\n{dirty}")
    return git("rev-parse", "HEAD")
