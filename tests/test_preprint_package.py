import importlib.util
import json

import pandas as pd

from digital_media_analysis.paths import PROJECT_ROOT


def load_script():
    spec = importlib.util.spec_from_file_location("preprint_package", PROJECT_ROOT / "scripts" / "18_preprint_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def h1a_keys(numbers: dict) -> dict:
    return {key: value for key, value in numbers.items() if key.startswith("hone a")}


def test_h1a_numbers_are_placeholders_before_the_pipeline(tmp_path):
    script = load_script()
    numbers = script.Numbers()
    status = script.h1a_numbers(numbers, tmp_path, tmp_path, tmp_path)
    keys = h1a_keys(numbers)
    assert status == "pending" and numbers["hone a status"] == "czeka na kodowanie stanowiska"
    assert all(value == script.PENDING for key, value in keys.items() if key != "hone a status")
    assert script.PENDING in script.h1_table(tmp_path)


def write_outputs(folder, passed: bool, with_trends: bool) -> None:
    pd.DataFrame([{"variable": "consensus_stance", "units": 30, "observed_agreement": 0.8, "kappa": 0.7, "kappa_low": 0.5,
                   "kappa_high": 0.85, "alpha": 0.69, "alpha_low": 0.5, "alpha_high": 0.84}]).to_csv(folder / "pilot_stance_agreement.csv", index=False)
    for split, posts in [("dev", 79), ("test", 78)]:
        pd.DataFrame({"metric": ["accuracy", "challenges:f1", "macro_f1", "kappa"],
                      "value": [0.9, 0.62 if passed else 0.3, 0.58, 0.71]}).to_csv(folder / f"stance_{split}_metrics.csv", index=False)
        run = {"posts": posts, "thresholds": {"relevance": 0.4, "supports": 0.3, "challenges": 0.6}}
        if split == "test":
            run["gate"] = {"passed": passed}
        (folder / f"stance_{split}_run.json").write_text(json.dumps(run), encoding="utf-8")
    trends = [{"hypothesis": "H1-B", "analysis": "primary", "outcome": "consensus", "odds_ratio_per_year": 1.03, "ci_low": 0.99,
               "ci_high": 1.06, "p_one_sided": 0.93, "units": 5154}]
    if with_trends:
        trends += [{"hypothesis": "H1-A", "analysis": analysis, "outcome": outcome, "odds_ratio_per_year": 1.05, "ci_low": 1.01,
                    "ci_high": 1.09, "p_one_sided": 0.004, "units": 1186}
                   for analysis in ["primary", "sensitivity_period", "only_science", "only_conspiracy"] for outcome in ["challenges", "supports"]]
    pd.DataFrame(trends).to_csv(folder / "confirmatory_trends.csv", index=False)
    yearly = [{"hypothesis": "H1-A", "outcome": "challenges", "group": "all", "year": year, "share": 0.1 if year < 2012 else 0.2,
               "low": 0.05, "high": 0.3} for year in range(2005, 2019)] if with_trends else []
    pd.DataFrame(yearly, columns=["hypothesis", "outcome", "group", "year", "share", "low", "high"]).to_csv(folder / "confirmatory_yearly.csv", index=False)


def test_h1a_numbers_fill_in_after_the_pipeline(tmp_path):
    script = load_script()
    write_outputs(tmp_path, passed=True, with_trends=True)
    numbers = script.Numbers()
    assert script.h1a_numbers(numbers, tmp_path, tmp_path, tmp_path) == "tested"
    assert numbers["hone a test challenges f"] == "0{,}62" and numbers["hone a gate"] == "spełniony"
    assert numbers["hone a challenges or"] == "1{,}05 [1{,}01; 1{,}09]" and numbers["hone a challenges p"] == "0{,}004"
    assert numbers["hone a relevant posts"] == "1186" and numbers["hone a challenges share early"] == "10\\,\\%"
    assert numbers["hone a thresholds"] == "relevance 0{,}40, supports 0{,}30, challenges 0{,}60"
    table = script.h1_table(tmp_path)
    assert script.PENDING not in table.split("H1-B")[0] and "1{,}05 [1{,}01; 1{,}09]" in table


def test_failed_gate_and_missing_test_have_their_own_status(tmp_path):
    script = load_script()
    write_outputs(tmp_path, passed=False, with_trends=False)
    numbers = script.Numbers()
    assert script.h1a_numbers(numbers, tmp_path, tmp_path, tmp_path) == "gate_failed"
    assert numbers["hone a gate"] == "niespełniony" and numbers["hone a challenges or"] == script.NOT_TESTED
    assert script.NOT_TESTED in script.h1_table(tmp_path, h1a_missing=script.NOT_TESTED).split("H1-B")[0]
    write_outputs(tmp_path, passed=True, with_trends=False)
    numbers = script.Numbers()
    assert script.h1a_numbers(numbers, tmp_path, tmp_path, tmp_path) == "awaiting_test"


def test_plan_c_numbers_wait_for_data_and_fill_in(tmp_path):
    script = load_script()
    numbers = script.Numbers()
    script.plan_c_numbers(numbers, tmp_path, tmp_path, tmp_path, tmp_path)
    assert numbers["plan c stance rule precision"] == script.WAITING and numbers["audit consensus j"] == script.WAITING
    pd.DataFrame([{"name": "stance_gold_IS", "rows": 60, "auto_share": 0.25, "control_rows": 4, "control_kept": 0.75},
                  {"name": "stance_gold_JP", "rows": 40, "auto_share": 0.5, "control_rows": 2, "control_kept": 1.0}]).to_csv(
        tmp_path / "llm_quality.csv", index=False)
    pd.DataFrame([{"annotator": "IS", "checked": 40, "changed": 4}]).to_csv(tmp_path / "gold_stance_ai_review.csv", index=False)
    pd.DataFrame([{"source": "pooled", "indicator": indicator, "sensitivity": 0.5, "specificity": 0.8, "youden": 0.3,
                   "youden_low": 0.1, "youden_high": 0.5, "valid": True, "positives": 20} for indicator in ["consensus", "alternative"]]
                 ).to_csv(tmp_path / "audit_error_rates.csv", index=False)
    numbers = script.Numbers()
    script.plan_c_numbers(numbers, tmp_path, tmp_path, tmp_path, tmp_path)
    assert numbers["plan c stance auto share"] == "35\,\%" and numbers["plan c stance rule precision"] == "5/6"
    assert numbers["plan c ai changed"] == "10\,\%" and numbers["audit consensus valid"] == "ważny"


def test_confusion_figure_is_a_placeholder_before_the_test(tmp_path):
    script = load_script()
    script.figure_stance_confusion(tmp_path / "confusion.png", tmp_path, tmp_path, tmp_path, tmp_path)
    assert (tmp_path / "confusion.png").exists()
