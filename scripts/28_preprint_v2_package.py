"""Results package of the new preprint (report/preprint_v2.tex; docs/plan_preprintu_v2.md, section 7).

Reads the frozen labels and scores of the blind AI annotation runs (annotations/ai_protocol/, scripts/26), the
planning power grid (annotations/hypotheses_v2/power_plan.csv, power_plan_values.json; scripts/17 --plan) and the
illustrative power gate (power_gate_plan.json; scripts/27 --plan), and writes report/numbers_v2.tex, the tables
report/tables/v2_*.tex and the figures report/figures/v2_*.png. The v1 macros stay in report/numbers.tex (scripts/18);
the new preprint reads both files.

Experiments: E1 = runs A and B (codebook 2.2), E2 = runs C and D (codebook 2.3), E3 = stance runs S1 and S2 against the
plan C reference, E4 = power with measurement error and the power gate. Intervals: Wilson for sensitivity and
specificity, percentile bootstrap (2000 draws, units resampled) for F1, MASI and kappa; kappa of runs from scripts/26.
Exploratory tests: McNemar for the correctness of cites_source on Wikipedia between runs A and C (B and D), whose rules
differ (codebook 2.3 adopted IS's reading of the same units, so the comparison is in-sample); the one-sided binomial
test that the sensitivity for `challenges` exceeds 0.8 (gate B2); Fisher's exact test of errors against the
`uncertain` flag. Results of the v2 confirmatory run do not exist yet and get the placeholder.
"""

import importlib.util
import json

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact
from sklearn.metrics import cohen_kappa_score, f1_score
from statsmodels.stats.contingency_tables import mcnemar

from digital_media_analysis import report
from digital_media_analysis.agreement import GRID, INK, INK_SECONDARY, SURFACE
from digital_media_analysis.charts import CATEGORICAL, MUTED
from digital_media_analysis.paths import (
    ANNOTATIONS_DIR,
    HYPOTHESES_V2_DIR,
    PROJECT_ROOT,
)
from digital_media_analysis.report import macro_file, tabular

REPORT_DIR = PROJECT_ROOT / "report"
PROTOCOL = ANNOTATIONS_DIR / "ai_protocol"
WAITING = r"\resWaiting"
SEED = 20261103
DRAWS = 2000
PLATFORMS = {"reddit": "Reddit", "wikipedia": "Wikipedia"}
RUNS = {"A": "2.2", "B": "2.2", "C": "2.3", "D": "2.3"}
STANCES = ["supports", "challenges", "neutral", "not_applicable"]


def load_protocol():
    spec = importlib.util.spec_from_file_location("ai_protocol", PROJECT_ROOT / "scripts" / "26_ai_protocol.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTO = load_protocol()


def number(value: float, digits: int = 2) -> str:
    return report.number(value, digits, english=True)


def p_value(value: float) -> str:
    return report.p_value(value, english=True)


def with_interval(values: list[float], digits: int = 2) -> str:
    value, low, high = values
    return f"{number(value, digits)} [{number(low, digits)}, {number(high, digits)}]"


class Numbers(dict):
    def put(self, key: str, value) -> None:
        if key in self:
            raise ValueError(f"Duplicate key {key}")
        self[key] = value


def wilson(hits: int, total: int) -> list[float]:
    found = binomtest(hits, total).proportion_ci(confidence_level=0.95, method="wilson")
    return [hits / total, found.low, found.high]


def bootstrap(statistic, frame: pd.DataFrame, rng: np.random.Generator) -> list[float]:
    values = [statistic(frame.iloc[rng.integers(0, len(frame), len(frame))]) for _ in range(DRAWS)]
    return [float(statistic(frame)), *np.percentile(values, [2.5, 97.5]).tolist()]


def scores(run: str) -> dict:
    return json.loads((PROTOCOL / f"scores_{run}.json").read_text(encoding="utf-8"))


def kappa_interval(estimate: dict) -> list[float]:
    return [estimate["value"], estimate["low"], estimate["high"]]


# --- E1 and E2: sources ------------------------------------------------------------------------------------------


def sources(numbers: Numbers, rng: np.random.Generator) -> pd.DataFrame:
    """Agreement of runs A-D with IS by platform, the stability of each pair and the McNemar comparisons."""
    reference = pd.concat([PROTO.coder(PROTO.LABELS_DIR / phase / "IS.csv", "is").assign(phase=phase) for phase in ["pilot", "gold"]])
    runs = {run: PROTO.run_labels(run, "ai").merge(reference, on=["platform", "unit_id"]) for run in RUNS}
    rows = []
    for run, frame in runs.items():
        for platform, part in frame.groupby("platform"):
            f1 = bootstrap(lambda data: f1_score(PROTO.cites(data["is_types"]), PROTO.cites(data["ai_types"]), zero_division=0), part, rng)
            masi = bootstrap(lambda data: np.mean([1 - PROTO.masi_distance(a, b) for a, b in zip(data["ai_types"], data["is_types"])]), part, rng)
            rows.append({"run": run, "codebook": RUNS[run], "platform": platform, "f1": f1, "masi": masi})
            numbers.put(f"e src {run} {platform} f1", with_interval(f1))
            numbers.put(f"e src {run} {platform} masi", with_interval(masi))
        result = scores(run)
        numbers.put(f"e src {run} wikipedia missed", str(sum(result["wikipedia_cites_missed_by_ai_is_labels"].values())))
        numbers.put(f"e src {run} personal kappa", number(result["ai_vs_is_per_code"]["personal"]["kappa"]))
        numbers.put(f"e src {run} uncertain", report.number(100 * result["uncertain_share"], 0, english=True) + "\\%")
    for later, earlier in (("B", "A"), ("D", "C")):
        stability = scores(later)[f"stability_vs_{earlier}"]
        for name in ("cites_kappa", "types_alpha_masi", "edit_kappa"):
            numbers.put(f"e src {earlier}{later} {name}", with_interval(kappa_interval(stability[name])))
    shifts = [scores(run)[f"stability_vs_{other}"]["cites_kappa"]["value"] for run, other in (("C", "A"), ("C", "B"), ("D", "A"), ("D", "B"))]
    numbers.put("e src codebook shift kappa min", number(min(shifts)))
    numbers.put("e src codebook shift kappa max", number(max(shifts)))
    for first, second in (("A", "C"), ("B", "D")):
        joined = runs[first].merge(runs[second][["platform", "unit_id", "ai_types"]].rename(columns={"ai_types": "second_types"}),
                                   on=["platform", "unit_id"])
        wiki = joined[joined["platform"].eq("wikipedia")]
        before = PROTO.cites(wiki["ai_types"]) == PROTO.cites(wiki["is_types"])
        after = PROTO.cites(wiki["second_types"]) == PROTO.cites(wiki["is_types"])
        table = pd.crosstab(before, after).reindex(index=[False, True], columns=[False, True], fill_value=0).to_numpy()
        numbers.put(f"e src mcnemar {first}{second} fixed", str(int(table[0, 1])))
        numbers.put(f"e src mcnemar {first}{second} broken", str(int(table[1, 0])))
        numbers.put(f"e src mcnemar {first}{second} p", p_value(mcnemar(table, exact=True).pvalue))
    for run in ("C", "D"):
        for name, met in scores(run)["k2_error_kappa_below_0_4"].items():
            numbers.put(f"e src {run} k two {name.replace('_v1', '')}", "met" if met else "not met")
    return pd.DataFrame(rows)


# --- E3: stance ----------------------------------------------------------------------------------------------------


def stance_metrics(truth: pd.Series, predicted: pd.Series, rng: np.random.Generator) -> dict:
    frame = pd.DataFrame({"truth": truth.to_numpy(), "predicted": predicted.to_numpy()})
    hits = int((frame["truth"].eq("challenges") & frame["predicted"].eq("challenges")).sum())
    positives = int(frame["truth"].eq("challenges").sum())
    rejections = int((frame["truth"].ne("challenges") & frame["predicted"].ne("challenges")).sum())
    return {"units": len(frame), "sensitivity": wilson(hits, positives), "specificity": wilson(rejections, len(frame) - positives),
            "f1": bootstrap(lambda data: f1_score(data["truth"].eq("challenges"), data["predicted"].eq("challenges")), frame, rng),
            "kappa": bootstrap(lambda data: cohen_kappa_score(data["truth"], data["predicted"]), frame, rng),
            "b2_p": float(binomtest(hits, positives, 0.8, alternative="greater").pvalue)}


def stance(numbers: Numbers, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    reference = PROTO.stance_reference()
    both = PROTO.stance_labels("S1", "one").merge(PROTO.stance_labels("S2", "two"), on="unit_id").merge(reference, on="unit_id")
    agreed = both[both["one_stance"] == both["two_stance"]]
    groups = {"S1": (both, "one_stance"), "S2": (both, "two_stance"), "agreed": (agreed, "one_stance")}
    rows = []
    for name, (frame, column) in groups.items():
        found = stance_metrics(frame["ref_stance"], frame[column], rng)
        rows.append({"labels": name, **found})
        for metric in ("sensitivity", "specificity", "f1", "kappa"):
            numbers.put(f"e stance {name} {metric}", with_interval(found[metric]))
        numbers.put(f"e stance {name} units", str(found["units"]))
        numbers.put(f"e stance {name} b two p", p_value(found["b2_p"]))
    numbers.put("e stance reference challenges", str(int(reference["ref_stance"].eq("challenges").sum())))
    numbers.put("e stance reference units", str(len(reference)))
    stability = scores("S2")["stability_vs_S1"]
    numbers.put("e stance kappa", with_interval(kappa_interval(stability["kappa"])))
    numbers.put("e stance agreement", report.number(100 * stability["agreement"], 0, english=True) + "\\%")
    for run, column in (("S1", "one"), ("S2", "two")):
        wrong = both[f"{column}_stance"] != both["ref_stance"]
        table = pd.crosstab(both[f"{column}_uncertain"], wrong).reindex(index=[0, 1], columns=[False, True], fill_value=0)
        numbers.put(f"e stance {run} errors flagged", f"{int(table.loc[1, True])} of {int(table.loc[1].sum())}")
        numbers.put(f"e stance {run} errors unflagged", f"{int(table.loc[0, True])} of {int(table.loc[0].sum())}")
        numbers.put(f"e stance {run} fisher p", p_value(fisher_exact(table.to_numpy())[1]))
        missed = both[both["ref_stance"].eq("challenges") & both[f"{column}_stance"].eq("neutral")]
        numbers.put(f"e stance {run} challenges as neutral", str(len(missed)))
    return pd.DataFrame(rows), agreed


# --- E4: power and the gate ------------------------------------------------------------------------------------------


# Macro key, variant, scenario of power_plan.csv, share (None: the only one) and the label in the table.
POWER_ROWS = [("h1 target ten", "H1", "Se 0.7, Sp 0.98 (gate B6)", 0.10, "stance, target instrument, p = 0.10"),
              ("h1 target fifteen", "H1", "Se 0.7, Sp 0.98 (gate B6)", 0.15, "stance, target instrument, p = 0.15"),
              ("h1 stance v one", "H1", "stance_v1", 0.10, "stance, stance\\_v1, p = 0.10"),
              ("h1 s one", "H1-S1", "GLiNER, alternative sources", None, "alternative sources (GLiNER)"),
              ("h1 s three", "H1-S3", "topic counts, no labels", None, "participation (no labels)"),
              ("h2 owner", "H2", "alternative by owner", None, "alternative sources by owner"),
              ("h2 domain", "H2", "alternative by domain", None, "alternative sources by domain"),
              ("h2 s one", "H2-S1", "domain category", None, "non-specialist sources")]


def power(numbers: Numbers) -> pd.DataFrame:
    plan_path = HYPOTHESES_V2_DIR / "power_plan.csv"
    values = json.loads((HYPOTHESES_V2_DIR / "power_plan_values.json").read_text(encoding="utf-8"))
    numbers.put("e power deff h one", number(values["h1_implied_design_effect"], 1))
    numbers.put("e power deff h two", number(values["h2_design_effect"]["without_bulk_revisions"]["design_effect"], 1))
    numbers.put("e power deff h two bulk", number(values["h2_design_effect"]["all_revisions"]["design_effect"], 0))
    numbers.put("e power alt owner share", number(100 * values["h2_alt_owner_share"], 2) + "\\%")
    plan = pd.read_csv(plan_path)
    rows = []
    for key, variant, scenario, share, label in POWER_ROWS:
        part = plan[plan["variant"].eq(variant) & plan["scenario"].eq(scenario)]
        if share is not None:
            part = part[part["share"].round(3).eq(share)]
        design = part["design_effect"].max()  # the realistic design effect of the grid (v1's)
        row = part[part["design_effect"].eq(design)].iloc[0]
        rows.append({"variant": variant, "label": label, "design_effect": design, "units": row["units_needed"],
                     "units_equivalence": row["units_needed_equivalence"]})
        numbers.put(f"e power {key} units", f"{int(row['units_needed']):,}")
        numbers.put(f"e power {key} units tost", f"{int(row['units_needed_equivalence']):,}")
    gate = json.loads((HYPOTHESES_V2_DIR / "power_gate_plan.json").read_text(encoding="utf-8"))
    for family, decision in gate["decision"].items():
        numbers.put(f"e gate plan {family} primary", decision["primary"] or "none")
    # The units the illustration assumed (scripts/27 --plan).
    numbers.put("e gate plan h1 units", f"{int(gate['inputs']['H1']['units']):,}")
    numbers.put("e gate plan h1 citing units", f"{int(gate['inputs']['H1-S1']['units']):,}")
    numbers.put("e gate plan h2 links", f"{int(gate['inputs']['H2']['units']):,}")
    confirmatory = HYPOTHESES_V2_DIR / "confirmatory_trends.csv"
    numbers.put("v two confirmatory status", "available" if confirmatory.exists() else WAITING)
    return pd.DataFrame(rows)


# --- Tables and figures ----------------------------------------------------------------------------------------------


def sources_table(frame: pd.DataFrame) -> str:
    rows = []
    for run, codebook in RUNS.items():
        cells = []
        for platform in PLATFORMS:
            row = frame[frame["run"].eq(run) & frame["platform"].eq(platform)].iloc[0]
            cells += [with_interval(row["f1"]), with_interval(row["masi"])]
        rows.append([run, codebook, *cells])
    return tabular(["Run", "Codebook", "Reddit F1", "Reddit MASI", "Wikipedia F1", "Wikipedia MASI"], rows, "llrrrr", groups=[2])


def stance_table(frame: pd.DataFrame) -> str:
    names = {"S1": "Run S1", "S2": "Run S2", "agreed": "Agreed labels (S1 = S2)"}
    rows = [[names[row["labels"]], str(row["units"]), with_interval(row["sensitivity"]), with_interval(row["specificity"]),
             with_interval(row["f1"]), with_interval(row["kappa"])] for row in frame.to_dict("records")]
    return tabular(["Labels", "Posts", "Sensitivity", "Specificity", "F1", r"$\kappa$ (4 values)"], rows, "lrrrrr")


def power_table(frame: pd.DataFrame) -> str:
    rows = [[row["variant"], row["label"], number(row["design_effect"], 1), f"{int(row['units']):,}", f"{int(row['units_equivalence']):,}"]
            for row in frame.to_dict("records")]
    return tabular(["Variant", "Indicator", "DEFF", "Units to detect SESOI", "Units for TOST"], rows, "llrrr", groups=[3, 5])


def _axes(axis) -> None:
    axis.set_facecolor(SURFACE)
    axis.grid(axis="x", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(colors=INK_SECONDARY, length=0, labelsize=8)
    for side in ["top", "right", "left"]:
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)


def figure_sources(frame: pd.DataFrame, path) -> None:
    """F1 of cites_source and MASI of source_types against IS with 95% intervals, runs A-D, one panel per platform."""
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(10, 3.0), sharex=True, facecolor=SURFACE)
    for axis, platform in zip(axes, PLATFORMS):
        _axes(axis)
        for position, (metric, label) in enumerate([("masi", "MASI (types)"), ("f1", "F1 cites_source")]):
            for offset, (colour, run) in zip([0.27, 0.09, -0.09, -0.27], zip(CATEGORICAL, RUNS)):
                value, low, high = frame[frame["run"].eq(run) & frame["platform"].eq(platform)].iloc[0][metric]
                axis.hlines(position + offset, low, high, color=colour, linewidth=2)
                axis.plot(value, position + offset, "o", color=colour, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5,
                          label=f"run {run} (codebook {RUNS[run]})" if position == 0 else None)
        axis.set_yticks([0, 1])
        axis.set_yticklabels(["MASI (types)", "F1 cites_source"], fontsize=8, color=INK)
        axis.set_xlim(0, 1)
        axis.set_title(f"{PLATFORMS[platform]}: AI runs against IS", loc="left", fontsize=10, color=INK)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, frameon=False, fontsize=8, labelcolor=INK, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.02))
    figure.supxlabel("agreement with the labels of IS (coded without AI), 95% bootstrap interval", fontsize=8, color=INK_SECONDARY)
    figure.tight_layout(rect=(0, 0, 1, 0.9))
    figure.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(figure)


def figure_stance_confusion(agreed: pd.DataFrame, path) -> None:
    """Agreed AI stance labels (S1 = S2) against the plan C reference: rows reference, columns AI."""
    import matplotlib.pyplot as plt

    table = pd.crosstab(agreed["ref_stance"], agreed["one_stance"]).reindex(index=STANCES, columns=STANCES, fill_value=0)
    figure, axis = plt.subplots(figsize=(4.8, 4.0), facecolor=SURFACE)
    axis.imshow(table.to_numpy(), cmap="Blues")
    for (row, column), value in np.ndenumerate(table.to_numpy()):
        axis.text(column, row, str(value), ha="center", va="center", fontsize=9,
                  color=SURFACE if value > table.to_numpy().max() / 2 else INK)
    labels = [name.replace("_", " ") for name in STANCES]
    axis.set_xticks(range(4), labels, rotation=30, ha="right", fontsize=8, color=INK)
    axis.set_yticks(range(4), labels, fontsize=8, color=INK)
    axis.set_xlabel("AI (agreed labels of runs S1 and S2)", fontsize=8, color=INK_SECONDARY)
    axis.set_ylabel("stance reference", fontsize=8, color=INK_SECONDARY)
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(figure)


def figure_power(path) -> None:
    """Power to detect the H1 smallest effect of interest against units, by instrument (planning values, DEFF of v1)."""
    import matplotlib.pyplot as plt

    from digital_media_analysis import power

    values = json.loads((HYPOTHESES_V2_DIR / "power_plan_values.json").read_text(encoding="utf-8"))
    design = values["h1_implied_design_effect"]
    slope = np.log(1.25) / 13
    units = np.linspace(5_000, 150_000, 120)
    curves = [("perfect instrument", 1.0, 1.0, 0.10), ("target instrument (Se 0.7, Sp 0.98)", 0.7, 0.98, 0.10),
              ("stance_v1 (Se 0.21, Sp 0.99)", 0.21, 0.987, 0.10),
              ("alternative sources, GLiNER (Se 0.81, Sp 0.77)", values["h1_gliner_alternative_sensitivity"],
               values["h1_gliner_alternative_specificity"], values["h1_alternative_true_share"])]
    figure, axis = plt.subplots(figsize=(7, 3.6), facecolor=SURFACE)
    _axes(axis)
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    for colour, (label, sensitivity, specificity, share) in zip(CATEGORICAL, curves):
        axis.plot(units / 1000, [power.trend_power(n, share, slope, 14, sensitivity, specificity, design) for n in units],
                  color=colour, linewidth=2, label=label)
    axis.axhline(0.8, color=MUTED, linewidth=1, linestyle="--")
    axis.set_ylim(0, 1)
    axis.set_xlabel("units in the analysis (thousands)", fontsize=8, color=INK_SECONDARY)
    axis.set_ylabel("power (one-sided, SESOI)", fontsize=8, color=INK_SECONDARY)
    axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="lower right")
    axis.set_title(f"H1: power with instrument error (DEFF {design:.1f}; share 0.10 for stance, {values['h1_alternative_true_share']:.2f} for sources)",
                   loc="left", fontsize=10, color=INK)
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(figure)


def main() -> None:
    rng = np.random.default_rng(SEED)
    numbers = Numbers()
    sources_frame = sources(numbers, rng)
    stance_frame, agreed = stance(numbers, rng)
    power_frame = power(numbers)
    (REPORT_DIR / "tables").mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "figures").mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "numbers_v2.tex").write_text(macro_file(numbers, "scripts/28_preprint_v2_package.py"), encoding="utf-8")
    (REPORT_DIR / "tables" / "v2_sources_runs.tex").write_text(sources_table(sources_frame), encoding="utf-8")
    (REPORT_DIR / "tables" / "v2_stance.tex").write_text(stance_table(stance_frame), encoding="utf-8")
    (REPORT_DIR / "tables" / "v2_power.tex").write_text(power_table(power_frame), encoding="utf-8")
    figure_sources(sources_frame, REPORT_DIR / "figures" / "v2_sources_runs.png")
    figure_stance_confusion(agreed, REPORT_DIR / "figures" / "v2_stance_confusion.png")
    figure_power(REPORT_DIR / "figures" / "v2_power.png")
    print(f"{len(numbers)} numbers -> {REPORT_DIR / 'numbers_v2.tex'}; tables v2_*.tex and figures v2_*.png in {REPORT_DIR}")


if __name__ == "__main__":
    main()
