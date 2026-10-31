"""Blind AI annotation protocol A1 (docs/protokol_anotacji_ai.md), practised on the 253 units IS coded without AI.

`blind --run A` (seed 20261031; run B: 20261032) draws a batch once: the fields people saw in the sheets, under
random codes and in random order, go to annotations/sheets/ai_protocol/blind_<run>.csv (outside git); the key
(code -> unit) and freeze_<run>.json with the hashes of the codebook and the protocol, taken before coding, go to
annotations/ai_protocol/. The annotator writes labels_<run>.csv there (code, source_types, edit_about_sources,
uncertain) and does not change it after the run.
`score --run A` compares the frozen labels with the labels of IS, with the earlier Claude labels of the pilot (JP's
pilot labels are AI first labels JP approved on 23.10.2026), with the blind AI coding of 27.10.2026, with the
instruments, whose errors should not fall on the same units (N6), and with every other run that has labels: K1 asks
for kappa of cites_source, alpha (MASI) of source_types and kappa of edit_about_sources of 0.8 or more (fixed on
31.10.2026 before the labels of run B were seen). Exploratory and unweighted.
"""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, f1_score

from digital_media_analysis.agreement import (
    Estimate,
    cohen_kappa,
    krippendorff_alpha,
    masi_distance,
)
from digital_media_analysis.codebook import NO_SOURCE, load_codebook
from digital_media_analysis.paths import (
    ANNOTATIONS_DIR,
    LABELS_DIR,
    PREDICTIONS_DIR,
    PROJECT_ROOT,
    SAMPLES_DIR,
    SHEETS_DIR,
)
from digital_media_analysis.validation import label_sets

PROTOCOL = ANNOTATIONS_DIR / "ai_protocol"
BLIND = SHEETS_DIR / "ai_protocol"
SEEDS = {"A": 20261031, "B": 20261032}
FROZEN = {"codebook": PROJECT_ROOT / "codebook" / "codebook.md", "protocol": PROJECT_ROOT / "docs" / "protokol_anotacji_ai.md"}
CONTROL_AI = ANNOTATIONS_DIR / "control" / "ai_blind_claude-opus-5-5.csv"
INSTRUMENTS = ["gliner_v1", "zeroshot_v1", "rules_v1"]
NONE = frozenset({NO_SOURCE})
K1_LIMIT = 0.8
K2_LIMIT = 0.4


def digest(path: Path, eol: bytes | None = None) -> str:
    """sha256 of the file, or of its text with every line ending set to `eol`."""
    data = path.read_bytes()
    if eol is not None:
        data = data.replace(b"\r\n", b"\n").replace(b"\n", eol)
    return hashlib.sha256(data).hexdigest()


def unchanged(path: Path, frozen: str) -> bool:
    """Whether the file still has its frozen content. Line endings depend on the checkout (core.autocrlf), not on the
    content: on 31.10.2026 the codebook was hashed with CRLF and the protocol with LF."""
    return frozen in {digest(path, eol) for eol in (None, b"\n", b"\r\n")}


def units() -> pd.DataFrame:
    """The units IS coded (pilot and gold) with the fields of the sheets (annotation_sheets.CONTENT_COLUMNS)."""
    wanted = pd.concat([pd.read_csv(LABELS_DIR / phase / "IS.csv", dtype=str)[["platform", "unit_id"]] for phase in ["pilot", "gold"]])
    wanted = set(map(tuple, wanted.to_numpy()))
    reddit = pd.read_csv(SAMPLES_DIR / "reddit_sample.csv", dtype=str)
    wiki = pd.read_csv(SAMPLES_DIR / "wikipedia_sample.csv", dtype=str, usecols=lambda column: column != "new_content")
    reddit = reddit[[("reddit", unit) in wanted for unit in reddit["unit_id"]]]
    wiki = wiki[[("wikipedia", unit) in wanted for unit in wiki["unit_id"]]]
    # As in gold.reddit_units: no link back to the post's own thread, relative links made absolute.
    own_thread = pd.Series([f"/comments/{post}/" in str(url) for post, url in zip(reddit["id"], reddit["url"])], index=reddit.index)
    link = reddit["url"].fillna("").where(~own_thread, "")
    link = link.where(~link.str.startswith("/"), "https://www.reddit.com" + link)
    return pd.concat([
        pd.DataFrame({"platform": "reddit", "unit_id": reddit["unit_id"], "group": "r/" + reddit["subreddit"],
                      "title": reddit["title"].fillna(""), "text": reddit["text"].fillna(""), "link": link}),
        pd.DataFrame({"platform": "wikipedia", "unit_id": wiki["unit_id"], "group": wiki["page"],
                      "title": "", "text": wiki["comment"].fillna(""), "link": ""}),
    ], ignore_index=True)


def blind(run: str) -> None:
    freeze = PROTOCOL / f"freeze_{run}.json"
    if freeze.exists():
        raise SystemExit(f"{freeze} exists: each run is drawn once, before coding.")
    batch = units()
    batch = batch.iloc[np.random.default_rng(SEEDS[run]).permutation(len(batch))].reset_index(drop=True)
    batch["code"] = [f"U{index + 1:03d}" for index in range(len(batch))]
    PROTOCOL.mkdir(parents=True, exist_ok=True)
    BLIND.mkdir(parents=True, exist_ok=True)
    batch[["code", "platform", "group", "title", "text", "link"]].to_csv(BLIND / f"blind_{run}.csv", index=False)
    batch[["code", "platform", "unit_id"]].to_csv(PROTOCOL / f"key_{run}.csv", index=False)
    record = {"created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "seed": SEEDS[run], "units": len(batch),
              **{f"{name}_sha256": digest(path) for name, path in FROZEN.items()}}
    freeze.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record), batch["platform"].value_counts().to_dict())


def rounded(value: float) -> float:
    return round(float(value), 3)


def kappa(reference: pd.Series, labels: pd.Series) -> float | None:
    """Cohen's kappa; None when both coders use one value only (undefined)."""
    if reference.nunique() < 2 and labels.nunique() < 2:
        return None
    return rounded(cohen_kappa_score(reference, labels))


def cites(types: pd.Series) -> pd.Series:
    return types.map(lambda labels: int(labels != NONE))


def masi(first: pd.Series, second: pd.Series) -> float:
    return rounded(np.mean([1 - masi_distance(a, b) for a, b in zip(first, second)]))


def readable(frame: pd.DataFrame) -> pd.DataFrame:
    """Set-valued `*_types` columns as their codes joined by ';'."""
    return frame.assign(**{column: frame[column].map(lambda labels: ";".join(sorted(labels))) for column in frame if column.endswith("_types")})


def coder(path: Path, name: str) -> pd.DataFrame:
    """Labels of a label file as `<name>_types` (sets) and `<name>_edit`, by platform and unit."""
    frame = pd.read_csv(path, dtype=str)
    frame = frame[frame["source_types"].fillna("").str.strip().ne("")]
    return pd.DataFrame({"platform": frame["platform"], "unit_id": frame["unit_id"], f"{name}_types": label_sets(frame["source_types"]),
                         f"{name}_edit": pd.to_numeric(frame["edit_about_sources"], errors="coerce")})


def run_labels(run: str, name: str) -> pd.DataFrame:
    """Frozen labels of a run by platform and unit: `<name>_types` (sets), `<name>_edit` and `<name>_uncertain`."""
    path = PROTOCOL / f"labels_{run}.csv"
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    key = pd.read_csv(PROTOCOL / f"key_{run}.csv", dtype=str)
    if sorted(raw["code"]) != sorted(key["code"]):
        raise SystemExit(f"{path} must label each of the {len(key)} units of the key exactly once.")
    labels = raw.merge(key, on="code")
    return pd.DataFrame({"platform": labels["platform"], "unit_id": labels["unit_id"], f"{name}_types": label_sets(labels["source_types"]),
                         f"{name}_edit": pd.to_numeric(labels["edit_about_sources"], errors="coerce"),
                         f"{name}_uncertain": labels["uncertain"].astype(int)})


def agreement(frame: pd.DataFrame, first: str, reference: str) -> dict:
    """Agreement of `first` with `reference` on cites_source (derived, R13) and source_types."""
    a, b = frame[f"{first}_types"], frame[f"{reference}_types"]
    return {"units": len(frame), "cites_agreement": rounded((cites(a) == cites(b)).mean()), "cites_kappa": kappa(cites(b), cites(a)),
            "cites_f1": rounded(f1_score(cites(b), cites(a), zero_division=0)), "types_exact": rounded((a == b).mean()), "types_masi": masi(a, b)}


def by_platform(frame: pd.DataFrame, first: str, reference: str) -> dict:
    return {platform: agreement(part, first, reference) for platform, part in frame.groupby("platform")}


def instrument_overlap(table: pd.DataFrame, instrument: str) -> dict:
    """N6: the AI annotator and the instrument against IS on the units the instrument predicted (dev and test)."""
    predictions = pd.concat([pd.read_csv(path, dtype=str) for split in ["dev", "test"]
                             if (path := PREDICTIONS_DIR / f"{instrument}_{split}.csv").exists()]).drop_duplicates(["platform", "unit_id"])
    predictions = pd.DataFrame({"platform": predictions["platform"], "unit_id": predictions["unit_id"],
                                "tool_types": label_sets(predictions["source_types"])})
    result = {}
    for platform, part in table.merge(predictions, on=["platform", "unit_id"]).groupby("platform"):
        errors = {name: {"cites": (cites(part[f"{name}_types"]) != cites(part["is_types"])).astype(int),
                         "types": (part[f"{name}_types"] != part["is_types"]).astype(int)} for name in ["ai", "tool"]}
        result[platform] = {
            "units": len(part),
            **{f"{name}_{what}": agreement(part, name, "is")[what] for name in ["ai", "tool"] for what in ["cites_f1", "types_masi"]},
            **{f"{name}_{kind}_errors": int(errors[name][kind].sum()) for name in ["ai", "tool"] for kind in ["cites", "types"]},
            **{f"kappa_{kind}_errors": kappa(errors["ai"][kind], errors["tool"][kind]) for kind in ["cites", "types"]},
            "ai_errors_shared": int((errors["ai"]["types"] & errors["tool"]["types"]).sum()),
        }
    return result


def interval(estimate: Estimate) -> dict:
    return {name: None if np.isnan(value) else rounded(value) for name, value in vars(estimate).items()}


def alpha_masi(frame: pd.DataFrame) -> Estimate:
    return krippendorff_alpha(list(zip(frame["ai_types"], frame["other_types"])), masi_distance)


def stability(both: pd.DataFrame) -> dict:
    """K1: agreement of this run (`ai_*`) with an earlier run of the AI annotator (`other_*`) on the same units."""
    wiki = both[both["platform"].eq("wikipedia")].dropna(subset=["ai_edit", "other_edit"])
    measures = {"cites_kappa": cohen_kappa(cites(both["ai_types"]), cites(both["other_types"])), "types_alpha_masi": alpha_masi(both),
                "edit_kappa": cohen_kappa(wiki["ai_edit"], wiki["other_edit"])}
    return {**{name: interval(value) for name, value in measures.items()},
            "k1_met": all(value.value >= K1_LIMIT for value in measures.values()),
            "by_platform": {platform: {**agreement(part, "ai", "other"), "types_alpha_masi": interval(alpha_masi(part))}
                            for platform, part in both.groupby("platform")},
            "per_code_kappa": {code: kappa(both["other_types"].map(lambda labels, c=code: c in labels),
                                           both["ai_types"].map(lambda labels, c=code: c in labels))
                               for code in load_codebook().category_codes if code != NO_SOURCE},
            "uncertain_kappa": kappa(both["other_uncertain"], both["ai_uncertain"])}


def score(run: str) -> None:
    labels_path = PROTOCOL / f"labels_{run}.csv"
    freeze = json.loads((PROTOCOL / f"freeze_{run}.json").read_text(encoding="utf-8"))
    reference = pd.concat([coder(LABELS_DIR / phase / "IS.csv", "is").assign(phase=phase) for phase in ["pilot", "gold"]])
    table = run_labels(run, "ai").merge(reference, on=["platform", "unit_id"], validate="one_to_one")

    # Labels hashed with LF line endings, as they were written, so a CRLF checkout gives the same hash.
    scores = {"run": run, "labels_sha256": digest(labels_path, b"\n"),
              "frozen_files_unchanged": {name: unchanged(path, freeze[f"{name}_sha256"]) for name, path in FROZEN.items()},
              "uncertain_share": rounded(table["ai_uncertain"].mean()), "ai_vs_is": by_platform(table, "ai", "is")}
    wiki = table[table["platform"].eq("wikipedia")].dropna(subset=["ai_edit", "is_edit"])
    scores["ai_vs_is"]["wikipedia_edit_about_sources"] = {
        "units": len(wiki), "agreement": rounded((wiki["ai_edit"] == wiki["is_edit"]).mean()),
        "kappa": kappa(wiki["is_edit"], wiki["ai_edit"]), "f1": rounded(f1_score(wiki["is_edit"], wiki["ai_edit"], zero_division=0))}
    scores["ai_vs_is_by_uncertain"] = {f"{platform}_uncertain_{flag}": agreement(part, "ai", "is")
                                       for (platform, flag), part in table.groupby(["platform", "ai_uncertain"])}
    scores["ai_vs_is_per_code"] = {
        code: {"is_units": int(table["is_types"].map(lambda labels, c=code: c in labels).sum()),
               "ai_units": int(table["ai_types"].map(lambda labels, c=code: c in labels).sum()),
               "kappa": kappa(table["is_types"].map(lambda labels, c=code: c in labels), table["ai_types"].map(lambda labels, c=code: c in labels))}
        for code in load_codebook().category_codes if code != NO_SOURCE}
    missed = table[table["platform"].eq("wikipedia") & cites(table["ai_types"]).eq(0) & cites(table["is_types"]).eq(1)]
    scores["wikipedia_cites_missed_by_ai_is_labels"] = missed["is_types"].map(lambda labels: ";".join(sorted(labels))).value_counts().to_dict()

    earlier = coder(LABELS_DIR / "pilot" / "JP.csv", "claude")
    pilot = table[table["phase"].eq("pilot")].merge(earlier, on=["platform", "unit_id"])
    scores["pilot"] = {"ai_vs_is": by_platform(pilot, "ai", "is"), "ai_vs_earlier_claude": by_platform(pilot, "ai", "claude"),
                       "is_vs_earlier_claude": by_platform(pilot, "is", "claude")}
    control = pd.read_csv(CONTROL_AI, dtype=str, keep_default_na=False)
    control = control[control["task"].eq("sources")]
    control = table.merge(pd.DataFrame({"unit_id": control["unit_id"], "control_types": label_sets(control["label"])}), on="unit_id")
    scores["control_27_10"] = {"units": len(control), "ai_vs_27_10_exact": rounded((control["ai_types"] == control["control_types"]).mean()),
                               "ai_vs_is_exact": rounded((control["ai_types"] == control["is_types"]).mean())}
    scores["instruments"] = {instrument: instrument_overlap(table, instrument) for instrument in INSTRUMENTS}
    scores["k2_error_kappa_below_0_4"] = {f"{instrument}_{platform}": all(value is not None and value < K2_LIMIT
                                                                           for value in (row["kappa_cites_errors"], row["kappa_types_errors"]))
                                          for instrument, rows in scores["instruments"].items() for platform, row in rows.items()}
    # Each later run is compared with the earlier ones (B with A).
    for other in sorted(SEEDS)[: sorted(SEEDS).index(run)]:
        if (PROTOCOL / f"labels_{other}.csv").exists():
            both = table.merge(run_labels(other, "other"), on=["platform", "unit_id"], validate="one_to_one")
            scores[f"stability_vs_{other}"] = stability(both)
            changed = both[(both["ai_types"] != both["other_types"]) | (both["ai_edit"].fillna(-1) != both["other_edit"].fillna(-1))]
            columns = {f"{side}_{field}": f"{name}_{field}" for side, name in [("ai", run), ("other", other)] for field in ["types", "edit", "uncertain"]}
            readable(changed).sort_values(["platform", "unit_id"])[["platform", "unit_id", "phase", "is_types", *columns]].rename(columns=columns).to_csv(
                PROTOCOL / f"disagreements_{run}_vs_{other}.csv", index=False, encoding="utf-8")

    (PROTOCOL / f"scores_{run}.json").write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")
    differences = table[(table["ai_types"] != table["is_types"]) | (table["ai_edit"].fillna(-1) != table["is_edit"].fillna(-1))]
    readable(differences).sort_values(["platform", "unit_id"])[
        ["platform", "unit_id", "phase", "ai_types", "is_types", "ai_edit", "is_edit", "ai_uncertain"]
    ].to_csv(PROTOCOL / f"disagreements_{run}.csv", index=False, encoding="utf-8")
    print(json.dumps(scores, indent=1, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["blind", "score"])
    parser.add_argument("--run", choices=sorted(SEEDS), default="A")
    args = parser.parse_args()
    blind(args.run) if args.step == "blind" else score(args.run)


if __name__ == "__main__":
    main()
