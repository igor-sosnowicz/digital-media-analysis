"""Variant A done automatically (amendment of 27.10.2026): draw the control samples, then score the blind second coding.

`draw` (once, seed 20261027) writes the sample key to annotations/control/control_sample.csv, the text-only blind
files to annotations/sheets/control/blind_<task>.csv (outside git) and the same rows, blind, as a sheet for people
(annotations/sheets/control/human_check.xlsx). The AI assistant then codes the blind files into
annotations/control/ai_blind_claude-opus-5-5.csv (task, unit_id, label, uncertain, reason).
`score` compares those labels with the sheet labels (stance, audit) and with the human consensus (sources).
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from digital_media_analysis import control_check as cc
from digital_media_analysis.paths import ANNOTATIONS_DIR

SHEETS = ANNOTATIONS_DIR / "sheets"
CONTROL = ANNOTATIONS_DIR / "control"
BLIND = SHEETS / "control"
KEY = CONTROL / "control_sample.csv"
AI_BLIND = CONTROL / "ai_blind_claude-opus-5-5.csv"
STANCE_SHEETS = [f"stance_{phase}_{who}.xlsx" for phase in ("gold", "enriched") for who in ("IS", "JP")]
AUDIT_SHEET = "audit_JP.xlsx"


def stance_rows() -> pd.DataFrame:
    """Stance sheet rows with their split (gold: sample manifest; enriched: enriched sample)."""
    manifest = pd.read_csv(ANNOTATIONS_DIR / "sample_manifest.csv", dtype=str)
    enriched = pd.read_csv(ANNOTATIONS_DIR / "hypotheses" / "stance_enriched_sample.csv", dtype=str)
    splits = pd.concat([manifest.loc[manifest["platform"].eq("reddit") & manifest["phase"].eq("gold"), ["unit_id", "split"]],
                        enriched[["unit_id", "split"]]]).drop_duplicates("unit_id")
    rows = pd.concat([cc.sheet_rows(SHEETS / name, "consensus_stance") for name in STANCE_SHEETS], ignore_index=True)
    return rows.merge(splits, on="unit_id", how="left")


def source_reference() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Source labels of people with the post text: the pilot posts IS and JP coded alike, and the gold Reddit posts
    one person coded. IS coded alone; JP's labels are AI first labels JP approved on 23.10.2026
    (docs/plan_walidacji.md), so `coder` keeps them apart (correction of 27.10.2026)."""
    labels = ANNOTATIONS_DIR / "labels"
    consensus = cc.human_consensus(pd.read_csv(labels / "pilot" / "IS.csv", dtype=str),
                                   pd.read_csv(labels / "pilot" / "JP.csv", dtype=str))
    gold = pd.concat([pd.read_csv(labels / "gold" / f"{who}.csv", dtype=str) for who in ("IS", "JP")])
    single = (gold.loc[gold["platform"].eq("reddit"), ["unit_id", "source_types", "annotator"]]
              .rename(columns={"source_types": "label"}).assign(coder=lambda d: "gold_" + d["annotator"]))
    posts = pd.concat([cc.sheet_rows(SHEETS / f"{phase}_{who}.xlsx", "source_types")
                       for phase in ("pilot", "gold") for who in ("JP", "IS")])
    posts = posts[cc.TEXT_COLUMNS].drop_duplicates("unit_id")
    return (consensus.merge(posts, on="unit_id").assign(sheet="labels/pilot", coder="pilot_consensus"),
            single.drop_duplicates("unit_id").merge(posts, on="unit_id").assign(sheet="labels/gold"))


def draw(force: bool) -> None:
    if KEY.exists() and not force:
        raise SystemExit(f"{KEY} exists: the control samples are drawn once (amendment of 27.10.2026).")
    samples = {"stance": cc.draw_stance(stance_rows()),
               "audit": cc.draw_simple(cc.sheet_rows(SHEETS / AUDIT_SHEET, "source_types"), cc.AUDIT_SIZE),
               "sources": cc.draw_sources(*source_reference())}
    CONTROL.mkdir(parents=True, exist_ok=True)
    BLIND.mkdir(parents=True, exist_ok=True)
    key = pd.concat([sample.assign(task=task)[["task", "unit_id", "sheet", "stratum", "N_h", "n_h", "weight"]]
                     for task, sample in samples.items()], ignore_index=True)
    key.to_csv(KEY, index=False, encoding="utf-8")
    with pd.ExcelWriter(BLIND / "human_check.xlsx") as writer:
        for task, sample in samples.items():
            blind = cc.blind(sample, task)
            blind.to_csv(BLIND / f"blind_{task}.csv", index=False, encoding="utf-8")
            blind.assign(label="", uncertain="", notes="", annotator="", verified="").to_excel(writer, sheet_name=task, index=False)
    for task, sample in samples.items():
        print(f"{task}: {len(sample)} units, strata {sample['stratum'].value_counts().to_dict()}")
    print(f"Key -> {KEY}; blind files and human_check.xlsx -> {BLIND}")


def score() -> None:
    key = pd.read_csv(KEY, dtype={"unit_id": str})
    coded = pd.read_csv(AI_BLIND, dtype=str, keep_default_na=False).rename(columns={"label": "blind"})
    missing = key.merge(coded, on=["task", "unit_id"], how="left")["blind"].isna().sum()
    if missing:
        raise SystemExit(f"{missing} sampled units have no blind label in {AI_BLIND}.")
    references = {"stance": stance_rows()[["unit_id", "label"]],
                  "audit": cc.sheet_rows(SHEETS / AUDIT_SHEET, "source_types")[["unit_id", "label"]],
                  "sources": pd.concat(source_reference())[["unit_id", "label", "coder"]].drop_duplicates("unit_id")}
    rows, differences = [], []
    for task, reference in references.items():
        frame = (key[key["task"].eq(task)].merge(reference, on="unit_id", how="left")
                 .merge(coded[coded["task"].eq(task)][["unit_id", "blind"]], on="unit_id", how="left"))
        multilabel = task != "stance"
        if task == "sources":
            # Strata by who coded the reference; IS alone is the only reference without AI help.
            frame = frame.assign(stratum=frame["coder"])
            rows += cc.score_sets(frame[frame["coder"].isin(["pilot_consensus", "gold_IS"])], "sources_is")
        rows += cc.score_stance(frame) if task == "stance" else cc.score_sets(frame, task)
        differences.append(cc.disagreements(frame, task, multilabel))
    scores = pd.DataFrame(rows)
    scores.to_csv(CONTROL / "control_scores.csv", index=False, encoding="utf-8")
    pd.concat(differences, ignore_index=True).to_csv(CONTROL / "control_disagreements.csv", index=False, encoding="utf-8")
    summary = {f"{row.task}.{row.measure}": round(row.value, 4) for row in scores.itertuples()}
    (CONTROL / "control_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(scores.round(3).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["draw", "score"])
    parser.add_argument("--force", action="store_true", help="draw again (only before any coding)")
    args = parser.parse_args()
    draw(args.force) if args.step == "draw" else score()


if __name__ == "__main__":
    main()
