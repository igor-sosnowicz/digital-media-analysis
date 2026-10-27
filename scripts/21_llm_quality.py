"""Quality of the automated annotation: agreement of A1 and A2 (plan B), and accuracy against people on the control rows.

For plan C (rule queues of scripts/22) there are no A1 and A2, so their columns
stay empty, and the control rows estimate the precision of the rules, per rule.

For one task: the queue of script 20 and the reviewed sheet. Reports the share
of rows A1 and A2 agree on and Cohen's kappa between them, the share accepted
automatically, and, on the control rows (a random 15% of the accepted ones,
checked by a person), the share where the person kept the suggestion, with a
bootstrap interval: an estimate of the error rate of the labels accepted
automatically. Also how often people changed the suggestion in the rest of the
queue. Each run updates its row in annotations/agreement/llm_quality.csv.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from digital_media_analysis import llm_annotation
from digital_media_analysis.agreement import cohen_kappa
from digital_media_analysis.annotation_sheets import _binary
from digital_media_analysis.paths import AGREEMENT_DIR

OUTPUT = AGREEMENT_DIR / "llm_quality.csv"


def kept_interval(kept: np.ndarray, samples: int = 2000, seed: int = 20261026) -> tuple[float, float]:
    if len(kept) == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    draws = [kept[rng.integers(0, len(kept), len(kept))].mean() for _ in range(samples)]
    return tuple(np.quantile(draws, [0.025, 0.975]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Row name in llm_quality.csv, e.g. stance_gold_JP.")
    parser.add_argument("--task", choices=llm_annotation.TASKS, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--reviewed", type=Path, required=True, help="The review sheet after people checked it.")
    parser.add_argument("--sheet")
    parser.add_argument("--key", nargs="+", default=["unit_id"])
    args = parser.parse_args()

    task = llm_annotation.TASKS[args.task]
    keys = {column: str for column in args.key}
    queue = pd.read_csv(args.queue, dtype=keys)
    reviewed = llm_annotation.read_rows(args.reviewed, args.sheet).astype(keys)
    reviewed = reviewed.assign(checked=[_binary(value, required=False)[0] == 1 for value in reviewed.get("verified", pd.Series(dtype=object))])
    frame = queue.merge(reviewed[[*args.key, task.target, "checked"]].rename(columns={task.target: "final"}), on=args.key, how="left")
    both = frame.dropna(subset=["label_a1", "label_a2"]) if "label_a1" in frame else frame.iloc[0:0]
    kappa = cohen_kappa(both["label_a1"].astype(str).tolist(), both["label_a2"].astype(str).tolist()) if len(both) else None
    checked = frame[frame["decided_by"].eq("human") & frame["checked"].fillna(False).astype(bool)]
    kept = checked["final"].astype(str).str.strip().eq(checked["suggestion"].astype(str))
    is_control = checked["queue_reason"].isin(["kontrola", "kontrola reguły"])
    control = kept[is_control].to_numpy(bool)
    if "rule" in checked:
        # Plan C: precision of each rule on its blind control rows.
        for rule, part in kept[is_control].groupby(checked.loc[is_control, "rule"]):
            print(f"  {rule}: {int(part.sum())}/{len(part)} kept")
    low, high = kept_interval(control)
    row = {
        "name": args.name, "task": args.task, "rows": len(frame), "a1_a2_agreement": frame["agree"].mean() if "agree" in frame else np.nan,
        "a1_a2_kappa": kappa.value if kappa else np.nan, "a1_a2_kappa_low": kappa.low if kappa else np.nan,
        "a1_a2_kappa_high": kappa.high if kappa else np.nan,
        "auto_share": frame["decided_by"].eq("auto").mean(), "queued": int(frame["decided_by"].eq("human").sum()),
        "checked": len(checked), "control_rows": len(control), "control_kept": control.mean() if len(control) else np.nan,
        "control_kept_low": low, "control_kept_high": high,
        "queue_changed": 1 - kept[~is_control & checked["suggestion"].notna()].mean() if len(checked) else np.nan,
    }
    table = pd.read_csv(OUTPUT) if OUTPUT.exists() else pd.DataFrame(columns=list(row))
    table = pd.concat([table[table["name"] != args.name], pd.DataFrame([row])], ignore_index=True)
    AGREEMENT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False, encoding="utf-8")
    print(pd.Series(row).to_string())


if __name__ == "__main__":
    main()
