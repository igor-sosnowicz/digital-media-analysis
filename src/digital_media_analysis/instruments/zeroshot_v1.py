"""Instrument zero-shot v1: a multilingual NLI model scores one hypothesis per codebook category.

The model (mDeBERTa-v3 trained on multilingual NLI) reads the unit text as the
premise and, for every source category, a hypothesis such as "The text refers to
a news outlet ...". A category's score is the model's probability of entailment
among entailment, neutral and contradiction (the zero-shot pipeline's
entailment-vs-contradiction ratio ignores neutral and scores almost every
hypothesis near 1). A unit gets every category whose score reaches the
platform's threshold, and `none` when no category does. Wikipedia units also get
`edit_about_sources` from a hypothesis of their own.

The hypothesis language and the thresholds were chosen on the dev split only
(`scripts/07_validate_instruments.py --tune`) and are frozen with the commit that
runs the test split.
"""

import pandas as pd

from digital_media_analysis.codebook import NO_SOURCE
from digital_media_analysis.instruments.labels import LABEL_SEPARATOR
from digital_media_analysis.instruments.unit_text import unit_texts

VERSION = "zeroshot_v1"
MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
REVISION = "b5113eb38ab63efdd7f280f8c144ea8b13f978ce"
EDIT = "edit_about_sources"

# One hypothesis per source category (every codebook code but `none`), with the
# examples of the codebook slide.
HYPOTHESES = {
    "en": {
        "scientific": "The text refers to a scientific publication, such as a journal article or a research paper (e.g. Nature, PubMed, Science).",
        "institutional": "The text refers to a scientific, statistical or public health institution, such as WHO, CDC, a university or a statistics office.",
        "media": "The text refers to a news outlet or magazine, such as BBC, Reuters, a newspaper or a news website.",
        "personal": "The author supports a claim with their own experience or with what a person they know told them.",
        "social_blog": "The text refers to social media, a video platform or a blog, such as YouTube, Twitter, Reddit or a blog post.",
        "encyclopedia": "The text refers to an encyclopedia or a dictionary, such as Wikipedia, Britannica or a dictionary.",
        "other": "The text refers to a company, a shop, a government office, a law or a non-governmental organization as a source.",
        "unknown": "The text refers to an unnamed source, such as \"studies show\" or \"experts say\", without saying which one.",
    },
    "pl": {
        "scientific": "Tekst powołuje się na publikację naukową, np. artykuł w czasopiśmie lub pracę badawczą (Nature, PubMed, Science).",
        "institutional": "Tekst powołuje się na instytucję naukową, statystyczną lub zdrowia publicznego, np. WHO, GUS, uczelnię.",
        "media": "Tekst powołuje się na media informacyjne, np. BBC, Reuters, gazetę lub portal informacyjny.",
        "personal": "Autor uzasadnia twierdzenie własnym doświadczeniem albo relacją znajomej osoby.",
        "social_blog": "Tekst powołuje się na media społecznościowe, serwis wideo lub blog, np. YouTube, Twitter, Reddit.",
        "encyclopedia": "Tekst powołuje się na encyklopedię lub słownik, np. Wikipedię, Britannikę, słownik języka polskiego.",
        "other": "Tekst powołuje się na firmę, sklep, urząd, akt prawny lub organizację pozarządową jako źródło.",
        "unknown": "Tekst powołuje się na nieokreślone źródło, np. „badania pokazują” albo „eksperci mówią”, bez wskazania jakie.",
    },
}
EDIT_HYPOTHESES = {
    "en": "This edit summary says that references, citations or footnotes were added, removed or fixed.",
    "pl": "Ten opis zmiany mówi, że dodano, usunięto lub poprawiono przypisy albo źródła.",
}
LANGUAGES = list(HYPOTHESES)

# Chosen on the dev split on 24.10.2026 (`scripts/07_validate_instruments.py --tune`):
# highest mean of weighted MASI and cites_source F1; edit_about_sources by its F1.
LANGUAGE = {"reddit": "en", "wikipedia": "pl"}
THRESHOLDS = {"reddit": 0.75, "wikipedia": 0.8}
EDIT_THRESHOLD = 0.15


def score(units: pd.DataFrame, languages: list[str] = LANGUAGES, batch_size: int = 16) -> pd.DataFrame:
    """Entailment probability for every unit and hypothesis: unit_id, platform, language, target, score.

    `target` is a category code or `edit_about_sources` (Wikipedia only).
    """
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, revision=REVISION).eval()
    entailment = next(index for index, name in model.config.id2label.items() if name.lower().startswith("entail"))

    texts = unit_texts(units)
    pairs = []
    for unit_id, platform in zip(units["unit_id"].astype(str), units["platform"]):
        for language in languages:
            targets = dict(HYPOTHESES[language])
            if platform == "wikipedia":
                targets[EDIT] = EDIT_HYPOTHESES[language]
            pairs += [(unit_id, platform, language, target, hypothesis) for target, hypothesis in targets.items()]

    from tqdm import tqdm

    # Batches of similar length need little padding, which is most of the CPU time.
    order = sorted(range(len(pairs)), key=lambda index: len(texts[pairs[index][0]]) + len(pairs[index][4]))
    scores = [0.0] * len(pairs)
    with torch.no_grad():
        for start in tqdm(range(0, len(order), batch_size), desc=f"{VERSION} NLI batches"):
            batch = order[start:start + batch_size]
            encoded = tokenizer(
                [texts[pairs[index][0]] for index in batch],
                [pairs[index][4] for index in batch],
                return_tensors="pt", padding=True, truncation="only_first", max_length=512,
            )
            for index, value in zip(batch, model(**encoded).logits.softmax(-1)[:, entailment].tolist()):
                scores[index] = value
    return pd.DataFrame(
        [(unit_id, platform, language, target) for unit_id, platform, language, target, _ in pairs],
        columns=["unit_id", "platform", "language", "target"],
    ).assign(score=scores)


def labels(
    scores: pd.DataFrame,
    language: dict[str, str] | None = None,
    thresholds: dict[str, float] | None = None,
    edit_threshold: float | None = None,
) -> pd.DataFrame:
    """Document labels from `score` output: unit_id, platform, cites_source, source_types, edit_about_sources."""
    language = language or LANGUAGE
    thresholds = thresholds or THRESHOLDS
    edit_threshold = EDIT_THRESHOLD if edit_threshold is None else edit_threshold
    rows = []
    for (unit_id, platform), unit_scores in scores.groupby(["unit_id", "platform"], sort=False):
        chosen = unit_scores[unit_scores["language"].eq(language[platform])].set_index("target")["score"]
        categories = chosen.drop(EDIT, errors="ignore")
        found = sorted(categories[categories >= thresholds[platform]].index)
        edit = int(chosen[EDIT] >= edit_threshold) if EDIT in chosen else pd.NA
        rows.append({
            "unit_id": unit_id,
            "platform": platform,
            "cites_source": int(bool(found)),
            "source_types": LABEL_SEPARATOR.join(found) or NO_SOURCE,
            "edit_about_sources": edit,
        })
    return pd.DataFrame(rows)
