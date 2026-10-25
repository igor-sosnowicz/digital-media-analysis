"""Charts of the v2 hypothesis tests (docs/hipotezy_v2.md), in the style of the project's other figures.

One axis per chart (never two y-scales), thin marks, recessive grid, text in
ink colours, series colours in the fixed categorical order below (validated
for colour-vision deficiency on the light surface; slots 3-5 are below 3:1
contrast, so every multi-series chart has a legend and the report a table).
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from digital_media_analysis.agreement import GRID, INK, INK_SECONDARY, SERIES, SURFACE

CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MUTED = "#898781"
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
OTHER = "inne"


def _figure(width: float, height: float, panels: int = 1):
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, panels, figsize=(width, height), squeeze=False, facecolor=SURFACE)
    return figure, list(axes[0])


def _style(axis, grid: str = "y") -> None:
    axis.set_facecolor(SURFACE)
    if grid:
        axis.grid(axis=grid, color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(colors=INK_SECONDARY, length=0, labelsize=8)
    for side in ["top", "right", "left"]:
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)


def _percent(axis, which: str = "y") -> None:
    from matplotlib.ticker import FuncFormatter

    formatter = FuncFormatter(lambda value, _: f"{value:.0%}".replace("%", " %"))
    (axis.yaxis if which == "y" else axis.xaxis).set_major_formatter(formatter)


def _save(figure, path) -> None:
    figure.tight_layout()
    if path is not None:
        figure.savefig(path, dpi=200, facecolor=SURFACE)


def _end_labels(axis, items: list[tuple[float, float, str]]) -> None:
    """Labels at line ends (x, y, text), moved apart vertically so they never overlap."""
    if not items:
        return
    low, high = axis.get_ylim()
    gap = (high - low) * 0.07
    placed = []
    for x, y, text in sorted(items, key=lambda item: item[1]):
        y = max(y, placed[-1] + gap) if placed else y
        placed.append(y)
        axis.text(x, y, f"  {text}", va="center", fontsize=8, color=INK, clip_on=False)


def _legend(axis, **kwargs) -> None:
    legend = axis.legend(frameon=False, fontsize=8, labelcolor=INK, **kwargs)
    return legend


def forest(table: pd.DataFrame, label: str, estimate: str, low: str, high: str, bound: float | None = None,
           section: str | None = None, xlabel: str = "iloraz szans na rok", path=None):
    """Dot-and-interval rows on a log scale, a line at 1 and the shaded equivalence band [1/bound, bound]."""
    rows = table.reset_index(drop=True)
    positions = np.arange(len(rows))[::-1]
    figure, (axis,) = _figure(7.5, 0.34 * len(rows) + 1.3)
    _style(axis, grid="x")
    if bound:
        axis.axvspan(1 / bound, bound, color=SERIES, alpha=0.08, linewidth=0, label=f"pas równoważności (OR {bound:.3f})".replace(".", ","))
    axis.axvline(1, color=INK_SECONDARY, linewidth=1)
    axis.hlines(positions, rows[low], rows[high], color=SERIES, linewidth=2)
    axis.plot(rows[estimate], positions, "o", color=SERIES, markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
    axis.set_xscale("log")
    axis.set_yticks(positions)
    axis.set_yticklabels(rows[label], fontsize=8, color=INK)
    if section:
        for index in range(1, len(rows)):
            if rows.loc[index, section] != rows.loc[index - 1, section]:
                axis.axhline(positions[index] + 0.5, color=GRID, linewidth=1)
    axis.set_xlabel(xlabel, fontsize=9, color=INK_SECONDARY)
    if bound:
        _legend(axis, loc="lower right")
    _save(figure, path)
    return figure


def specification_curve(table: pd.DataFrame, choices: Sequence[str], alpha: float = 0.05, path=None):
    """Sorted estimates with intervals (significant ones in the series colour) above a matrix of the choices used."""
    import matplotlib.pyplot as plt

    rows = table[table["estimate"].notna()].sort_values("estimate", ignore_index=True)
    options = [(choice, option) for choice in choices for option in dict.fromkeys(rows[choice])]
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(8, 2.6 + 0.22 * len(options)), sharex=True, facecolor=SURFACE,
                                         gridspec_kw={"height_ratios": [2.2, 0.22 * len(options) + 0.3]})
    x = np.arange(len(rows))
    significant = rows["p_one_sided"] < alpha
    colours = np.where(significant, SERIES, MUTED)
    _style(top)
    top.axhline(1, color=INK_SECONDARY, linewidth=1)
    top.vlines(x, rows["ci_low"], rows["ci_high"], colors=colours, linewidth=1.5)
    top.scatter(x, rows["estimate"], c=colours, s=22, zorder=3, edgecolors=SURFACE, linewidths=1)
    top.set_yscale("log")
    top.set_ylabel("efekt na rok", fontsize=9, color=INK_SECONDARY)
    top.set_title(f"{int(significant.sum())} z {len(rows)} specyfikacji istotnych (p < {alpha})".replace(".", ","),
                  loc="left", fontsize=10, color=INK)
    _style(bottom, grid="")
    for row_index, (choice, option) in enumerate(options):
        used = rows[choice].eq(option).to_numpy()
        bottom.scatter(x[used], np.full(used.sum(), row_index), s=10, color=INK_SECONDARY)
    bottom.set_yticks(range(len(options)))
    bottom.set_yticklabels([f"{choice}: {option}" for choice, option in options], fontsize=7, color=INK)
    bottom.invert_yaxis()
    bottom.set_xticks([])
    _save(figure, path)
    return figure


def yearly_panels(yearly: pd.DataFrame, panel: str, titles: dict | None = None, share: str = "share",
                  low: str = "low", high: str = "high", columns: int = 4, path=None):
    """Small multiples, one per panel value, of a yearly share with its interval band, on a shared y-scale."""
    import matplotlib.pyplot as plt

    names = list(dict.fromkeys(yearly[panel]))
    rows_count = int(np.ceil(len(names) / columns))
    figure, axes = plt.subplots(rows_count, min(columns, len(names)), figsize=(3.2 * min(columns, len(names)), 2.4 * rows_count),
                                squeeze=False, sharey=True, facecolor=SURFACE)
    top = float(np.nanmax(yearly[high])) * 1.1 if len(yearly) else 1
    for axis, name in zip(axes.flat, names):
        part = yearly[yearly[panel].eq(name)].sort_values("year")
        _style(axis)
        axis.fill_between(part["year"], part[low], part[high], color=SERIES, alpha=0.12, linewidth=0)
        axis.plot(part["year"], part[share], color=SERIES, linewidth=2)
        axis.plot(part["year"], part[share], "o", color=SERIES, markersize=4, markeredgecolor=SURFACE, clip_on=False)
        axis.set_ylim(0, top)
        _percent(axis)
        axis.set_title((titles or {}).get(name, str(name)), loc="left", fontsize=9, color=INK)
    for axis in list(axes.flat)[len(names):]:
        axis.set_visible(False)
    _save(figure, path)
    return figure


def _top_categories(table: pd.DataFrame, category: str, value: str, limit: int) -> list:
    totals = table.groupby(category)[value].sum().sort_values(ascending=False)
    return list(totals.index[:limit])


def composition(table: pd.DataFrame, x: str, category: str, value: str, limit: int = 7, xlabel: str = "rok", path=None):
    """100% stacked areas of `value` by category over `x`; categories beyond `limit` fold into 'inne'."""
    keep = _top_categories(table, category, value, limit)
    data = table.assign(**{category: table[category].where(table[category].isin(keep), OTHER)})
    pivot = data.pivot_table(index=x, columns=category, values=value, aggfunc="sum", fill_value=0)
    pivot = pivot[[name for name in [*keep, OTHER] if name in pivot]]
    shares = pivot.div(pivot.sum(axis=1), axis=0)
    figure, (axis,) = _figure(8, 3.6)
    _style(axis)
    colours = CATEGORICAL[: len(keep)] + ([MUTED] if OTHER in shares else [])
    axis.stackplot(shares.index, shares.T.to_numpy(), labels=shares.columns, colors=colours, edgecolor=SURFACE, linewidth=1.5)
    axis.set_ylim(0, 1)
    axis.set_xlim(shares.index.min(), shares.index.max())
    _percent(axis)
    axis.set_xlabel(xlabel, fontsize=9, color=INK_SECONDARY)
    _legend(axis, loc="upper left", bbox_to_anchor=(1.01, 1))
    _save(figure, path)
    return figure


def decomposition(table: pd.DataFrame, label: str, path=None):
    """Change of a share split into within-group and composition parts: bars around zero, one row per part."""
    parts = [("total", "zmiana łączna"), ("within", "w obrębie grup"), ("composition", "zmiana składu")]
    rows = [(f"{row[label]}: {name}", row[part]) for _, row in table.iterrows() for part, name in parts]
    figure, (axis,) = _figure(7, 0.32 * len(rows) + 1.2)
    _style(axis, grid="x")
    positions = np.arange(len(rows))[::-1]
    values = np.array([value for _, value in rows])
    axis.barh(positions, values, height=0.55, color=SERIES)
    axis.axvline(0, color=INK_SECONDARY, linewidth=1)
    span = max(np.abs(values).max(), 0.01)
    for position, value in zip(positions, values):
        axis.text(value + (span * 0.03 if value >= 0 else -span * 0.03), position, f"{value * 100:+.1f} pp".replace(".", ","),
                  va="center", ha="left" if value >= 0 else "right", fontsize=8, color=INK)
    axis.set_xlim(-span * 1.4, span * 1.4)
    axis.set_yticks(positions)
    axis.set_yticklabels([name for name, _ in rows], fontsize=8, color=INK)
    axis.set_xlabel("zmiana udziału (punkty procentowe)", fontsize=9, color=INK_SECONDARY)
    _save(figure, path)
    return figure


def lines(table: pd.DataFrame, x: str, series: str, value: str, low: str | None = None, high: str | None = None,
          marker: float | None = None, marker_label: str = "", ylabel: str = "", percent: bool = True, path=None):
    """A few series (at most four) over `x`, with interval bands, a legend and labels at the line ends."""
    names = list(dict.fromkeys(table[series]))[:4]
    figure, (axis,) = _figure(7.5, 3.4)
    _style(axis)
    ends = []
    for colour, name in zip(CATEGORICAL, names):
        part = table[table[series].eq(name)].sort_values(x)
        if low and high:
            axis.fill_between(part[x], part[low], part[high], color=colour, alpha=0.1, linewidth=0)
        axis.plot(part[x], part[value], color=colour, linewidth=2, label=str(name))
        ends.append((part[x].iloc[-1], part[value].iloc[-1], str(name)))
    _end_labels(axis, ends)
    if marker is not None:
        axis.axvline(marker, color=INK_SECONDARY, linewidth=1)
        axis.text(marker, axis.get_ylim()[1], f" {marker_label}", va="top", fontsize=8, color=INK_SECONDARY)
    if percent:
        _percent(axis)
    axis.set_ylabel(ylabel, fontsize=9, color=INK_SECONDARY)
    _legend(axis, loc="upper left")
    _save(figure, path)
    return figure


def survival_curves(curves: pd.DataFrame, group: str, xlabel: str = "dni od dodania", path=None):
    """Kaplan-Meier step curves per group with confidence bands."""
    figure, (axis,) = _figure(7, 3.4)
    _style(axis)
    for colour, (name, part) in zip(CATEGORICAL, curves.groupby(group)):
        axis.fill_between(part["time"], part["low"], part["high"], step="post", color=colour, alpha=0.1, linewidth=0)
        axis.step(part["time"], part["survival"], where="post", color=colour, linewidth=2, label=str(name))
    axis.set_ylim(0, 1.02)
    _percent(axis)
    axis.set_xlabel(xlabel, fontsize=9, color=INK_SECONDARY)
    axis.set_ylabel("odsetek linków nadal w artykule", fontsize=9, color=INK_SECONDARY)
    _legend(axis, loc="lower left")
    _save(figure, path)
    return figure


def stacked_bars(table: pd.DataFrame, x: str, category: str, value: str, order: Sequence[str] | None = None, path=None):
    """100% stacked columns of `value` by category for each `x`, with a 2 px surface gap between segments."""
    pivot = table.pivot_table(index=x, columns=category, values=value, aggfunc="sum", fill_value=0)
    columns = [name for name in (order or pivot.columns) if name in pivot]
    shares = pivot[columns].div(pivot[columns].sum(axis=1), axis=0)
    figure, (axis,) = _figure(8, 3.6)
    _style(axis)
    bottom = np.zeros(len(shares))
    labels = [str(index) for index in shares.index]
    for colour, name in zip(CATEGORICAL + [MUTED] * 8, columns):
        axis.bar(labels, shares[name], bottom=bottom, width=0.6, color=colour, edgecolor=SURFACE, linewidth=2, label=str(name))
        bottom += shares[name].to_numpy()
    axis.set_ylim(0, 1)
    _percent(axis)
    _legend(axis, loc="upper left", bbox_to_anchor=(1.01, 1))
    _save(figure, path)
    return figure


def event_timeline(events: pd.DataFrame, time: str, row: str, colour_by: str, limit: int = 25, path=None):
    """One dot per event (e.g. an added alternative link) on a time axis, one row per page, coloured by category."""
    pages = events[row].value_counts().index[:limit]
    data = events[events[row].isin(pages)]
    categories = list(dict.fromkeys(data[colour_by]))
    figure, (axis,) = _figure(8, 0.3 * len(pages) + 1.4)
    _style(axis, grid="x")
    positions = {name: index for index, name in enumerate(pages[::-1])}
    for colour, name in zip(CATEGORICAL + [MUTED] * 8, categories):
        part = data[data[colour_by].eq(name)]
        axis.scatter(pd.to_datetime(part[time]), part[row].map(positions), s=36, color=colour, edgecolors=SURFACE, linewidths=1.5,
                     label=str(name), zorder=3)
    axis.set_yticks(list(positions.values()))
    axis.set_yticklabels(list(positions), fontsize=8, color=INK)
    _legend(axis, loc="upper left", bbox_to_anchor=(1.01, 1))
    _save(figure, path)
    return figure


def heatmap(matrix: pd.DataFrame, label: str = "udział", path=None):
    """Rows x columns of shares in one hue from light to dark; empty cells stay blank."""
    from matplotlib.colors import LinearSegmentedColormap

    figure, (axis,) = _figure(1.0 + 0.5 * matrix.shape[1], 0.25 * matrix.shape[0] + 1.4)
    colormap = LinearSegmentedColormap.from_list("sequential", SEQUENTIAL)
    image = axis.imshow(matrix.to_numpy(dtype=float), aspect="auto", cmap=colormap, vmin=0)
    axis.set_xticks(range(matrix.shape[1]))
    axis.set_xticklabels(matrix.columns, fontsize=8, color=INK)
    axis.set_yticks(range(matrix.shape[0]))
    axis.set_yticklabels(matrix.index, fontsize=7, color=INK)
    axis.tick_params(length=0)
    for side in axis.spines.values():
        side.set_visible(False)
    bar = figure.colorbar(image, ax=axis, fraction=0.04)
    bar.set_label(label, fontsize=8, color=INK_SECONDARY)
    bar.outline.set_visible(False)
    _save(figure, path)
    return figure


def labelled_scatter(table: pd.DataFrame, x: str, y: str, label: str, xlabel: str, ylabel: str, path=None):
    """Points with a text label each (e.g. years), for a correlation of two yearly measures."""
    figure, (axis,) = _figure(5, 4)
    _style(axis, grid="both")
    axis.scatter(table[x], table[y], s=40, color=SERIES, edgecolors=SURFACE, linewidths=2, zorder=3)
    for _, row in table.iterrows():
        axis.text(row[x], row[y], f" {row[label]}", fontsize=8, color=INK, va="center")
    axis.set_xlabel(xlabel, fontsize=9, color=INK_SECONDARY)
    axis.set_ylabel(ylabel, fontsize=9, color=INK_SECONDARY)
    _save(figure, path)
    return figure


def power_curves(table: pd.DataFrame, x: str, planned: float | None = None, path=None):
    """Power to detect the smallest effect and to show equivalence under no effect, against sample size; line at 0.8."""
    figure, (axis,) = _figure(7, 3.4)
    _style(axis)
    axis.set_ylim(0, 1.02)
    ends = []
    for colour, (column, name) in zip(CATEGORICAL, [("power", "wykrycie efektu"), ("power_equivalence", "wykazanie braku efektu")]):
        axis.plot(table[x], table[column], color=colour, linewidth=2, marker="o", markersize=5, label=name)
        ends.append((table[x].iloc[-1], table[column].iloc[-1], name))
    _end_labels(axis, ends)
    axis.axhline(0.8, color=INK_SECONDARY, linewidth=1, linestyle=(0, (4, 3)))
    if planned is not None:
        axis.axvline(planned, color=INK_SECONDARY, linewidth=1)
        axis.text(planned, 0.02, " plan", fontsize=8, color=INK_SECONDARY)
    axis.set_ylim(0, 1.02)
    _percent(axis)
    axis.set_xlabel(x, fontsize=9, color=INK_SECONDARY)
    axis.set_ylabel("moc", fontsize=9, color=INK_SECONDARY)
    _legend(axis, loc="lower center")
    _save(figure, path)
    return figure


def columns(table: pd.DataFrame, x: str, value: str, ylabel: str, marker: float | None = None, marker_label: str = "", path=None):
    """One series of counts as columns over `x` (e.g. references added per year), with an optional event line."""
    figure, (axis,) = _figure(7.5, 3.2)
    _style(axis)
    axis.bar(table[x].astype(float), table[value], width=0.7, color=SERIES, edgecolor=SURFACE, linewidth=2)
    if marker is not None:
        axis.axvline(marker, color=INK_SECONDARY, linewidth=1)
        axis.text(marker, axis.get_ylim()[1], f" {marker_label}", va="top", fontsize=8, color=INK_SECONDARY)
    axis.set_ylabel(ylabel, fontsize=9, color=INK_SECONDARY)
    _save(figure, path)
    return figure
