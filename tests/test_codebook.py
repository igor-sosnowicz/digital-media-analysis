import pytest
import yaml
from pydantic import ValidationError

from digital_media_analysis.codebook import Codebook, load_codebook
from digital_media_analysis.instruments import rules_v1
from digital_media_analysis.paths import CODEBOOK_PATH


@pytest.fixture
def raw_codebook() -> dict:
    return yaml.safe_load(CODEBOOK_PATH.read_text(encoding="utf-8"))


def test_codebook_loads_and_validates():
    codebook = load_codebook()
    assert len(codebook.category_codes) == 10
    assert {variable.code for variable in codebook.variables_for("wikipedia")} == {
        "cites_source", "source_types", "edit_about_sources",
    }
    assert {variable.code for variable in codebook.variables_for("reddit")} == {
        "cites_source", "source_types",
    }


def test_markdown_render_is_up_to_date():
    rendered = load_codebook().to_markdown()
    committed = CODEBOOK_PATH.with_suffix(".md").read_text(encoding="utf-8")
    assert rendered == committed, "codebook.md is stale; run `make codebook`."


def test_v1_mapping_targets_codebook_categories():
    codes = set(load_codebook().category_codes)
    for mapping in (rules_v1.REDDIT_CATEGORY_MAP, rules_v1.WIKIPEDIA_CATEGORY_MAP):
        assert {code for code in mapping.values() if code is not None} <= codes


def test_v1_mapping_covers_every_v1_category():
    assert set(rules_v1.REDDIT_CATEGORY_MAP) == {
        *rules_v1.REDDIT_REFERENCE_PATTERNS, "link/domena", "sygnał powołania",
    }
    assert set(rules_v1.WIKIPEDIA_CATEGORY_MAP) | rules_v1.WIKIPEDIA_NON_CITATION == {
        *rules_v1.WIKIPEDIA_SOURCE_CATEGORIES,
        "inna domena zewnętrzna",
        "powołanie bez wskazanego źródła",
        "odniesienie techniczne Wikipedii",
    }


def test_negative_example_without_reason_is_rejected(raw_codebook):
    raw_codebook["categories"][0]["negative"][0]["why"] = ""
    with pytest.raises(ValidationError, match="needs a 'why'"):
        Codebook.model_validate(raw_codebook)


def test_reference_to_undefined_rule_is_rejected(raw_codebook):
    raw_codebook["rules"] = [rule for rule in raw_codebook["rules"] if rule["code"] != "R3"]
    with pytest.raises(ValidationError, match="R3"):
        Codebook.model_validate(raw_codebook)


def test_duplicate_category_code_is_rejected(raw_codebook):
    raw_codebook["categories"][1]["code"] = raw_codebook["categories"][0]["code"]
    with pytest.raises(ValidationError, match="Duplicate category"):
        Codebook.model_validate(raw_codebook)
