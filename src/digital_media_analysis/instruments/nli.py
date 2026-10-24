"""Entailment probabilities from the multilingual NLI model used by the zero-shot instruments."""

from collections.abc import Sequence

MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
REVISION = "b5113eb38ab63efdd7f280f8c144ea8b13f978ce"


def entailment(premises: Sequence[str], hypotheses: Sequence[str], batch_size: int = 16, desc: str = "NLI") -> list[float]:
    """P(entailment) among entailment, neutral and contradiction for each (premise, hypothesis) pair."""
    import torch
    from tqdm import tqdm
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, revision=REVISION).eval()
    label = next(index for index, name in model.config.id2label.items() if name.lower().startswith("entail"))
    # Batches of similar length need little padding, which is most of the CPU time.
    order = sorted(range(len(premises)), key=lambda index: len(premises[index]) + len(hypotheses[index]))
    scores = [0.0] * len(premises)
    with torch.no_grad():
        for start in tqdm(range(0, len(order), batch_size), desc=desc):
            batch = order[start:start + batch_size]
            encoded = tokenizer(
                [premises[index] for index in batch], [hypotheses[index] for index in batch],
                return_tensors="pt", padding=True, truncation="only_first", max_length=512,
            )
            for index, value in zip(batch, model(**encoded).logits.softmax(-1)[:, label].tolist()):
                scores[index] = value
    return scores
