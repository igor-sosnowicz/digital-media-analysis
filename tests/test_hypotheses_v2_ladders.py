import importlib.util

import numpy as np
import pandas as pd
import pytest

from digital_media_analysis.paths import PROJECT_ROOT


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), PROJECT_ROOT / "scripts" / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCRIPT = load_script("16_test_hypotheses_v2.py")
RULES = {"exclude_v1_units": False, "v1_reddit_frames": [],
         "h2": {"bulk_revision_links": 20, "non_specialist_categories": ["media", "social_blog", "other"], "group_sesoi_odds_ratio": 1.5,
                "survival_hazard_ratio": 1.25, "marginal_share": 0.02, "institution_null_share": 0.25}}


def links(seed: int = 7, pages: int = 60, per_page: int = 40) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = pages * per_page
    health = np.repeat(np.arange(pages) % 2, per_page)
    category = np.where(rng.random(n) < np.where(health == 1, 0.5, 0.3), "media", "scientific")
    alt_domain = (rng.random(n) < 0.01).astype(int)
    return pd.DataFrame({
        "url": [f"u{i}" for i in range(n)], "article": np.repeat(np.arange(pages), per_page), "revid": np.arange(n) // 2,
        "title": np.repeat([f"page {i}" for i in range(pages)], per_page), "year": rng.integers(2020, 2027, n),
        "health": health, "first_addition": True, "category": category, "alt_owner": (rng.random(n) < 0.002).astype(int),
        "alt_domain": alt_domain, "owner_type": np.where(alt_domain == 1, "institution", ""),
        "days_present": rng.exponential(300, n), "censored": rng.random(n) < 0.6,
    }).assign(year_c=lambda frame: frame["year"] - 2020)


def test_h2_ladder_reports_every_variant_with_the_v2_columns():
    rows = SCRIPT.h2_ladder(links(), {"period": [2020, 2026], "sesoi_period_odds_ratio": 1.5}, RULES)
    found = {item["variant"]: item for item in rows}
    assert set(found) == {"H2-S1", "H2-S2", "H2-S3", "H2-S4", "H2-S5"}
    assert found["H2-S2"]["estimate"] > 1 and found["H2-S2"]["p_one_sided"] < 0.05
    assert found["H2-S4"]["p_one_sided"] < 0.05 and found["H2-S4"]["effect"] == "share"
    assert found["H2-S3"]["effect"] == "HR" and np.isfinite(found["H2-S3"]["tost_p_tost"])


def test_decide_adjusts_primary_tests_with_holm_and_gives_verdicts():
    table = pd.DataFrame([
        {"hypothesis": "H1", "analysis": "primary", "outcome": "challenges", "effect": "OR", "p_one_sided": 0.03, "tost_p_tost": 0.4},
        {"hypothesis": "H1", "analysis": "only posts", "outcome": "challenges", "effect": "OR", "p_one_sided": 0.01, "tost_p_tost": 0.4},
        {"hypothesis": "H2", "analysis": "H2-S1: x", "outcome": "non_specialist", "effect": "OR", "p_one_sided": 0.6, "tost_p_tost": 0.01,
         "variant": "H2-S1"},
        {"hypothesis": "H2", "analysis": "H2-S4: x", "outcome": "alt_owner", "effect": "share", "p_one_sided": 0.001, "tost_p_tost": np.nan,
         "variant": "H2-S4"},
    ])
    decided = SCRIPT.decide(table, {"H1": "primary", "H2-S1": "primary", "H2-S4": "secondary"}, 0.05)
    by_analysis = decided.set_index("analysis")
    assert by_analysis.loc["primary", "role"] == "primary"
    assert by_analysis.loc["primary", "p_one_sided_holm"] == pytest.approx(0.06)
    assert by_analysis.loc["primary", "verdict"] == "nierozstrzygnięta"
    assert by_analysis.loc["H2-S1: x", "verdict"] == "obalona: brak efektu"
    assert by_analysis.loc["H2-S4: x", "verdict"] == "potwierdzona"
    assert by_analysis.loc["only posts", "role"] == "analysis" and by_analysis.loc["only posts", "verdict"] == ""
