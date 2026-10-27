"""Plan C: deterministic codebook rules label the cases they decide alone; people code the rest.

No language model takes part. `rule_label` returns a label only when a rule of
the codebook settles the unit without judgement (e.g. a post with no reference
to science has no stance on science, R14; a revert is not a source, R9);
otherwise it returns None and the unit goes to a person. A random control share
of the rule labels also goes to a person, blind (the sheet shows no rule label),
so the precision of each rule can be estimated (`p_review` as in plan B). The
queue has the columns `llm_annotation.write_queue` expects, so the review sheets,
readers, weights and the validity gate of plan B work unchanged. Rules and
procedure: docs/hipotezy.md (amendment of 26.10.2026, plan C) and docs/plan_c_reguly.md.
"""

import re
from collections.abc import Sequence

import numpy as np
import pandas as pd

from digital_media_analysis import topics
from digital_media_analysis.instruments.unit_text import OWN_MEDIA_HOSTS, link_host
from digital_media_analysis.stance import SCIENCE_TERMS

CONTROL_SHARE = 0.15
SEED = 20261026
HUMAN_REASON = "do zakodowania"
SCIENCE_SUBREDDITS = {"science", "skeptic"}

# Words that may introduce a source; a post with one of them is never decided by a rule.
SOURCE_CUES = re.compile(
    r"(?<!\w)(?:according|source\w*|stud(?:y|ies)|research\w*|report\w*|via|says|said|survey\w*|poll\w*|data|paper|journal"
    r"|article|news|wg|według|źródł\w*|badani\w*|raport\w*|sondaż\w*|https?://\S+)(?!\w)",
    re.IGNORECASE,
)
SECTION_PREFIX = re.compile(r"/\*.*?\*/")
REVERT = re.compile(r"^\s*(?:Anulowanie wersji|Wycofano (?:edycj|ostatni)|Bot:)", re.IGNORECASE)
MINOR_TAGS = {"drobne redakcyjne", "drobne techniczne", "drobne merytoryczne", "int.", "lit.", "jęz.", "kat.", "akt.", "+",
              "drobne", "literówka", "literówki", "styl", "interpunkcja", "dr red", "drobne red."}
REFERENCE_TAG = "źródła/przypisy"


def _text(record: dict, columns: Sequence[str]) -> str:
    return " ".join(str(record.get(column) or "") for column in columns if str(record.get(column) or "") not in {"nan", "None"}).strip()


def _wikipedia_tags(comment: str) -> list[str] | None:
    """The comma-separated tags of an edit summary without its section prefix, or None when it holds free text."""
    rest = SECTION_PREFIX.sub("", comment).strip()
    tags = [tag.strip().lower() for tag in rest.split(",") if tag.strip()]
    return tags if all(tag in MINOR_TAGS | {REFERENCE_TAG} for tag in tags) else None


def rule_label(task: str, record: dict, topic_set: dict | None = None) -> tuple[str | None, int | None, str]:
    """(label, binary variable, rule) when a codebook rule decides the unit alone, else (None, None, '')."""
    if task == "stance":
        # Posts of science subreddits are about science by default, so only other subreddits can be ruled out.
        if str(record.get("subreddit") or "") in SCIENCE_SUBREDDITS:
            return None, None, ""
        text = _text(record, ["tytuł", "treść", "link"])
        if not SCIENCE_TERMS.search(text) and not topics.matches(text, topic_set or topics.load_topics()):
            return "not_applicable", None, "R14: brak odniesienia do nauki"
        return None, None, ""
    if task == "sources_reddit":
        title, body = _text(record, ["tytuł"]), _text(record, ["treść"])
        link = _text(record, ["link"])
        if SOURCE_CUES.search(f"{title} {body}"):
            return None, None, ""
        if link and link_host(link) in OWN_MEDIA_HOSTS and not body:
            return "none", None, "R3: własny obraz lub film"
        if not link and not body:
            return "none", None, "R13: sam tytuł bez powołania"
        return None, None, ""
    if task == "sources_wikipedia":
        comment = _text(record, ["opis zmiany"])
        if REVERT.search(comment) and not re.search(r"źród|przypis", comment, re.IGNORECASE):
            return "none", 0, "R9: rewert lub komunikat bota"
        tags = _wikipedia_tags(comment)
        if tags is not None:
            return "none", int(REFERENCE_TAG in tags), "R9/R10: same znaczniki edycji" if tags else "R9: sam prefiks sekcji"
        return None, None, ""
    if task == "error_cause":
        instrument, variable, error = (str(record.get(column) or "") for column in ("instrument", "variable", "error"))
        text, link = _text(record, ["tekst"]), _text(record, ["link"])
        if (instrument == "rules_v1" and variable == "cites_source" and error == "FN" and record.get("platform") == "reddit"
                and link):
            return "pominięte pole url", None, "v1 nie czyta pola url posta z linkiem"
        if instrument == "rules_v1" and variable == "cites_source" and error == "FP" and _wikipedia_tags(text) is not None \
                and REFERENCE_TAG in text:
            return "znacznik edycji", None, "same znaczniki z „źródła/przypisy”"
        without_links = re.sub(r"\[\[[^\]]*\]\]", "", text).strip(" ,")
        if error == "FP" and "[[WP:" in text and _wikipedia_tags(without_links) is not None:
            return "skrót WP:", None, "poza linkami [[…]] same znaczniki"
        return None, None, ""
    if task == "domain":
        links = pd.to_numeric(record.get("links"), errors="coerce")
        category = str(record.get("category") or "")
        if category not in {"social_blog", "unclassified", "unknown"} and links < 5:
            return category, None, "domena poza priorytetem przeglądu: kategoria bez zmian"
        return None, None, ""
    raise ValueError(f"Unknown task {task!r}")


def queue(records: pd.DataFrame, task: str, key_columns: Sequence[str], control_share: float = CONTROL_SHARE,
          seed: int = SEED) -> pd.DataFrame:
    """Per row: the rule label (if any), who decides, why, and p_review; a control share of rule labels goes to a person."""
    rng = np.random.default_rng(seed)
    topic_set = topics.load_topics()
    rows = []
    for record in records.to_dict("records"):
        label, binary, rule = rule_label(task, record, topic_set)
        decided = label is not None
        control = decided and rng.random() < control_share
        rows.append({
            **{column: str(record[column]) for column in key_columns},
            "rule": rule, "suggestion": label, "suggestion_binary": binary,
            "decided_by": "human" if (not decided or control) else "auto",
            "queue_reason": ("kontrola reguły" if control else "") if decided else "brak reguły",
            "p_review": control_share if decided else 1.0,
            "reason": rule,
        })
    return pd.DataFrame(rows)


def sheet_view(rule_queue: pd.DataFrame) -> pd.DataFrame:
    """What the review sheet shows: rule labels only on rows decided by a rule; people code the rest blind."""
    human = rule_queue["decided_by"].eq("human")
    return rule_queue.assign(
        suggestion=rule_queue["suggestion"].where(~human, None),
        suggestion_binary=rule_queue["suggestion_binary"].where(~human, None),
        queue_reason=rule_queue["queue_reason"].where(~human, HUMAN_REASON),
        reason=rule_queue["reason"].where(~human, HUMAN_REASON),
    )
