"""H1 v2: analysis sample, instrument labels and the human validation of stance_v2, distrust_v1 and topics_v1.

Steps (docs/hipotezy_v2.md), each a flag:
- default: the analysis sample from the downloaded frame (annotations/hypotheses_v2/h1_sample.csv,
  authors as pseudonyms), distrust_v1 labels and stance_v2 scores (cached in
  data/model_cache/); stance labels only once stance_v2 is tuned (TUNED = True);
- --validation-annotators A B: the validation sample (the same number of units
  per period, a third for tuning) and one blind workbook per person;
- --import-validation: the filled workbooks, agreement of the two people and the
  reference (agreed labels; disputes are listed and settled in
  annotations/labels/h1v2_validation/adjudicated.csv);
- --tune: stance_v2 thresholds on the dev part of the validation sample;
- --evaluate: once, on the frozen and committed instruments, the test part:
  metrics per period, the validity gate and the error counts for the corrected trend.
Needs the `ml` dependency group for stance_v2.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from itertools import product

import numpy as np
import pandas as pd

from digital_media_analysis import agreement, h1_frame, hypotheses, topics, validation
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.config_reader import get_hypotheses_v2
from digital_media_analysis.instruments import distrust_v1, stance_v2
from digital_media_analysis.paths import (
    FRAME_LABELS_DIR,
    HYPOTHESES_V2_DIR,
    LABELS_DIR,
    MODEL_CACHE_DIR,
    RAW_H1V2_DIR,
    SHEETS_DIR,
)
from digital_media_analysis.prereg import require_committed

SEED = 20261025
STANCES = ["supports", "challenges", "neutral", "not_applicable"]
LABELS = LABELS_DIR / "h1v2_validation"
GRID = [round(value, 2) for value in np.arange(0.2, 0.91, 0.05)]


def load_frame() -> pd.DataFrame:
    posts = pd.concat([pd.read_csv(path, dtype={"id": str}) for path in sorted(RAW_H1V2_DIR.glob("posts-*.csv"))], ignore_index=True)
    comment_paths = sorted(RAW_H1V2_DIR.glob("comments-*.csv"))
    comments = pd.concat([pd.read_csv(path, dtype={"id": str, "link_id": str}) for path in comment_paths], ignore_index=True)
    return h1_frame.units(posts, comments)


def salt() -> str:
    path = RAW_H1V2_DIR / "pseudonym_salt.txt"
    if not path.exists():
        import secrets

        path.write_text(secrets.token_hex(16), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip()


def instrument_input(units: pd.DataFrame) -> pd.DataFrame:
    text = (units["title"].fillna("") + "\n" + units["text"].fillna("")).str.strip()
    return pd.DataFrame({"unit_id": units["unit_id"], "topics": units["topics"], "text": text.str[:2000]})


def reference() -> pd.DataFrame:
    """Agreed validation labels, with the adjudicated ones in place of disputes."""
    labels = pd.concat([pd.read_csv(path, dtype=str, keep_default_na=False) for path in sorted(LABELS.glob("*.csv"))
                        if path.stem != "adjudicated"], ignore_index=True)
    agreed = labels.groupby("unit_id").filter(lambda rows: rows[["consensus_topic", "consensus_stance"]].drop_duplicates().shape[0] == 1)
    agreed = agreed.drop_duplicates("unit_id")
    adjudicated_path = LABELS / "adjudicated.csv"
    if adjudicated_path.exists():
        adjudicated = pd.read_csv(adjudicated_path, dtype=str, keep_default_na=False)
        agreed = pd.concat([agreed[~agreed["unit_id"].isin(adjudicated["unit_id"])], adjudicated], ignore_index=True)
    return agreed[["unit_id", "consensus_topic", "consensus_stance"]]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-annotators", nargs="+", default=[])
    parser.add_argument("--import-validation", action="store_true")
    parser.add_argument("--tune", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite existing validation workbooks.")
    parser.add_argument("--refresh", action="store_true", help="Recompute stance_v2 scores instead of reading the cache.")
    args = parser.parse_args()
    settings = get_hypotheses_v2()["h1"]
    codebook = load_codebook()
    HYPOTHESES_V2_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_LABELS_DIR.mkdir(parents=True, exist_ok=True)
    found_topics = topics.load_topics()

    frame = load_frame()
    sample = h1_frame.analysis_sample(frame, settings["period"], int(settings["units_per_cell"]), SEED)
    sample = sample.assign(author_id=h1_frame.pseudonym(sample["author"], salt()))
    public = ["unit_id", "kind", "author_id", "group", "year", "day", "day_weight", "weight", "topics"]
    sample[public].to_csv(HYPOTHESES_V2_DIR / "h1_sample.csv", index=False, encoding="utf-8")
    print(f"H1 v2 sample: {len(sample)} units ({sample['kind'].value_counts().to_dict()}), "
          f"{len(h1_frame.panel_authors(sample, int(settings['panel_min_years'])))} panel authors")

    inputs = instrument_input(sample)
    distrust_v1.labels(inputs.set_index("unit_id")["text"]).to_csv(FRAME_LABELS_DIR / "h1v2_distrust_v1.csv", index=False, encoding="utf-8")
    scores = hypotheses.cached_scores(MODEL_CACHE_DIR / "stance_v2_h1v2.csv", inputs,
                                      lambda units: stance_v2.score(units, found_topics), refresh=args.refresh)
    if stance_v2.TUNED:
        stance_v2.labels(scores, inputs["unit_id"]).to_csv(FRAME_LABELS_DIR / "h1v2_stance_v2.csv", index=False, encoding="utf-8")

    drawn_path = HYPOTHESES_V2_DIR / "h1_validation_sample.csv"
    if args.validation_annotators:
        drawn = h1_frame.validation_sample(sample, settings["validation_periods"], int(settings["validation_units_per_period"]), SEED)
        drawn[["unit_id", "kind", "group", "year", "period", "split", "inclusion", "weight", "order"]].to_csv(drawn_path, index=False, encoding="utf-8")
        for annotator in args.validation_annotators:
            path = SHEETS_DIR / f"h1v2_validation_{annotator}.xlsx"
            if path.exists() and not args.force:
                parser.error(f"{path} exists and may hold labels; use --force to overwrite.")
            h1_frame.write_validation_workbook(path, annotator, drawn, codebook)
            print(f"Wrote {path} ({len(drawn)} units)")

    if args.import_validation:
        failed = False
        for path in sorted(SHEETS_DIR.glob("h1v2_validation_*.xlsx")):
            labels, problems = h1_frame.read_validation_workbook(path, codebook)
            if problems:
                failed = True
                print(f"{path.name}: " + "; ".join(problems[:20]))
                continue
            LABELS.mkdir(parents=True, exist_ok=True)
            labels.to_csv(LABELS / f"{path.stem.removeprefix('h1v2_validation_')}.csv", index=False, encoding="utf-8")
            print(f"{path.name}: {len(labels)} labels")
        if failed:
            sys.exit("Fix the problems above and import again.")
        labels = pd.concat([pd.read_csv(path, dtype=str, keep_default_na=False) for path in sorted(LABELS.glob("*.csv"))
                            if path.stem != "adjudicated"], ignore_index=True)
        if labels["annotator"].nunique() >= 2:
            rows = []
            for variable in ["consensus_topic", "consensus_stance"]:
                matrix = labels.pivot(index="unit_id", columns="annotator", values=variable)
                units = [[value for value in row if isinstance(value, str) and value] for row in matrix.itertuples(index=False)]
                estimate = agreement.krippendorff_alpha([row for row in units if len(row) >= 2])
                rows.append({"variable": variable, "units": sum(len(row) >= 2 for row in units), "alpha": estimate.value,
                             "alpha_low": estimate.low, "alpha_high": estimate.high})
            pd.DataFrame(rows).to_csv(HYPOTHESES_V2_DIR / "h1_validation_agreement.csv", index=False, encoding="utf-8")
            disputes = labels.groupby("unit_id").filter(lambda rows: rows[["consensus_topic", "consensus_stance"]].drop_duplicates().shape[0] > 1)
            disputes.to_csv(HYPOTHESES_V2_DIR / "h1_validation_disputes.csv", index=False, encoding="utf-8")
            print(pd.DataFrame(rows).round(3).to_string(index=False))

    if args.tune or args.evaluate:
        drawn = pd.read_csv(drawn_path, dtype={"unit_id": str})
        truth = drawn.merge(reference(), on="unit_id")
        truth = truth.assign(weight=truth["weight"] / truth["inclusion"])
    if args.tune:
        dev = truth[truth["split"].eq("dev")]
        rows = []
        for supports, challenges in product(GRID, GRID):
            predicted = stance_v2.labels(scores, dev["unit_id"], {"supports": supports, "challenges": challenges})
            values = validation.nominal_metrics(dev["consensus_stance"], predicted["consensus_stance"], dev["weight"], STANCES)
            rows.append({"supports": supports, "challenges": challenges, "challenges_f1": values["challenges:f1"],
                         "macro_f1": values["macro_f1"], "kappa": values["kappa"]})
        grid = pd.DataFrame(rows).sort_values(["challenges_f1", "macro_f1"], ascending=False)
        grid.to_csv(HYPOTHESES_V2_DIR / "h1_stance_v2_tuning.csv", index=False, encoding="utf-8")
        print(f"Best on dev (F1 challenges, then macro-F1):\n{grid.head(3).round(3).to_string(index=False)}\n"
              "Set THRESHOLDS and TUNED = True in instruments/stance_v2.py, commit, then run --evaluate once.")
    if args.evaluate:
        commit = require_committed(["src/digital_media_analysis/instruments/stance_v2.py", "src/digital_media_analysis/instruments/distrust_v1.py",
                                    "src/digital_media_analysis/topics.py", "codebook/topics.yaml", "scripts/14_label_h1_v2.py"])
        result_path = HYPOTHESES_V2_DIR / "h1_instrument_test.json"
        if not stance_v2.TUNED:
            sys.exit("stance_v2 is not tuned yet (TUNED = False).")
        if result_path.exists():
            sys.exit(f"{result_path.name} exists: the test part is evaluated once.")
        test = truth[truth["split"].eq("test")]
        stance = stance_v2.labels(scores, test["unit_id"])
        distrust = distrust_v1.labels(instrument_input(sample.set_index("unit_id").loc[test["unit_id"]].reset_index()).set_index("unit_id")["text"])
        topic = topics.label(instrument_input(sample.set_index("unit_id").loc[test["unit_id"]].reset_index()).set_index("unit_id")["text"], found_topics)
        rows, counts = [], {}
        for period, part in [("all", test), *test.groupby("period")]:
            mask = test["unit_id"].isin(part["unit_id"]).to_numpy()
            values = validation.nominal_metrics(part["consensus_stance"], stance["consensus_stance"][mask], part["weight"], STANCES)
            y = part["consensus_stance"].eq("challenges").to_numpy()
            p = stance["consensus_stance"][mask].eq("challenges").to_numpy()
            d = distrust["distrust"][mask].astype(bool).to_numpy()
            counts[period] = {"tp": int((y & p).sum()), "fn": int((y & ~p).sum()), "tn": int((~y & ~p).sum()), "fp": int((~y & p).sum())}
            topic_values = validation.nominal_metrics(part["consensus_topic"], topic["consensus_topic"][mask], part["weight"],
                                                      [*found_topics, topics.NO_TOPIC])
            rows.append({"period": period, "units": len(part), "stance_challenges_f1": values["challenges:f1"], "stance_kappa": values["kappa"],
                         "stance_macro_f1": values["macro_f1"], "distrust_f1": 2 * (y & d).sum() / max(y.sum() + d.sum(), 1),
                         "topic_accuracy": topic_values["accuracy"], "topic_kappa": topic_values["kappa"]})
        table = pd.DataFrame(rows)
        table.to_csv(HYPOTHESES_V2_DIR / "h1_instrument_test.csv", index=False, encoding="utf-8")
        overall = table.iloc[0]
        gate = settings["gate"]
        passed = bool(overall["stance_challenges_f1"] >= gate["challenges_f1"] and overall["stance_kappa"] >= gate["kappa"])
        result_path.write_text(json.dumps({"created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": commit,
                                           "thresholds": stance_v2.THRESHOLDS, "gate": gate, "gate_passed": passed,
                                           "challenges_counts": counts}, indent=2) + "\n", encoding="utf-8")
        print(table.round(3).to_string(index=False))
        print(f"Validity gate {'passed' if passed else 'NOT passed'} ({gate}).")


if __name__ == "__main__":
    main()
