"""Load, validate and render the shared annotation codebook (`codebook/codebook.yaml`)."""

import re
from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from pydantic import BaseModel, Field, model_validator

from digital_media_analysis.paths import CODEBOOK_PATH

Platform = Literal["reddit", "wikipedia"]
RULE_REFERENCE = re.compile(r"\bR\d+\b")
# Codes are English identifiers; names and definitions stay Polish.
CODE_PATTERN = re.compile(r"^[a-z][a-z_]*$")
# The `source_types` code of a unit without any source reference. It stands
# alone, and `cites_source` is 0 exactly when it is the label (rule R13).
NO_SOURCE = "none"


class Unit(BaseModel):
    platform: Platform
    unit: str
    text: str
    note: str = ""


class Variable(BaseModel):
    code: str
    name: str
    # nominal: one of `values`, whose keys are English codes like category codes.
    type: Literal["binary", "multilabel", "nominal"]
    platforms: list[Platform]
    question: str
    values: dict[str, str] = {}
    requires: str = ""
    # How the variable follows from coded ones; derived variables are not in the sheet.
    derived: str = ""


class Example(BaseModel):
    platform: Platform
    text: str
    why: str = ""


class Category(BaseModel):
    code: str
    name: str
    definition: str
    include: list[str]
    exclude: list[str]
    positive: list[Example]
    negative: list[Example]

    @model_validator(mode="after")
    def _check_examples(self) -> "Category":
        if not self.positive or not self.negative:
            raise ValueError(f"Category {self.code!r} needs positive and negative examples.")
        if any(not example.why for example in self.negative):
            raise ValueError(f"Every negative example of {self.code!r} needs a 'why'.")
        return self


class Rule(BaseModel):
    code: str
    text: str


class AnnotationColumn(BaseModel):
    name: str
    description: str


class ChangelogEntry(BaseModel):
    version: str
    date: date
    changes: str


class Codebook(BaseModel):
    title: str
    version: str
    date: date
    status: str
    construct_definition: str = Field(alias="construct")
    units: list[Unit]
    variables: list[Variable]
    categories: list[Category]
    rules: list[Rule]
    annotation_columns: list[AnnotationColumn]
    changelog: list[ChangelogEntry]

    @model_validator(mode="after")
    def _check_consistency(self) -> "Codebook":
        for kind, codes in (
            ("variable", [variable.code for variable in self.variables]),
            ("category", self.category_codes),
            ("rule", [rule.code for rule in self.rules]),
        ):
            duplicates = sorted({code for code in codes if codes.count(code) > 1})
            if duplicates:
                raise ValueError(f"Duplicate {kind} codes: {duplicates}")

        codes = [variable.code for variable in self.variables] + self.category_codes
        if invalid := sorted(code for code in codes if not CODE_PATTERN.match(code)):
            raise ValueError(f"Codes must be English identifiers (lowercase letters and _): {invalid}")
        if NO_SOURCE not in self.category_codes:
            raise ValueError(f"The categories must include {NO_SOURCE!r} for units without a source.")
        for variable in self.variables:
            if variable.type == "nominal":
                if len(variable.values) < 2:
                    raise ValueError(f"Nominal variable {variable.code!r} needs at least two values.")
                if invalid := sorted(value for value in variable.values if not CODE_PATTERN.match(value)):
                    raise ValueError(f"Values of {variable.code!r} must be English identifiers: {invalid}")

        known_rules = {rule.code for rule in self.rules}
        referenced_rules = set(RULE_REFERENCE.findall(self.model_dump_json()))
        if unknown := referenced_rules - known_rules:
            raise ValueError(f"Referenced rules are not defined: {sorted(unknown)}")

        if not self.changelog or self.changelog[-1].version != self.version:
            raise ValueError(f"The last changelog entry must describe version {self.version}.")
        return self

    @property
    def category_codes(self) -> list[str]:
        return [category.code for category in self.categories]

    def variable(self, code: str) -> Variable:
        """The variable with this code."""
        for variable in self.variables:
            if variable.code == code:
                return variable
        raise KeyError(f"No variable {code!r} in the codebook.")

    def variables_for(self, platform: Platform) -> list[Variable]:
        return [variable for variable in self.variables if platform in variable.platforms]

    def variables_frame(self, platform: Platform) -> pd.DataFrame:
        return pd.DataFrame(
            {"zmienna": variable.code, "nazwa": variable.name, "typ": variable.type, "pytanie": variable.question}
            for variable in self.variables_for(platform)
        )

    def categories_frame(self) -> pd.DataFrame:
        """One row per category, for display in notebooks and slides."""
        return pd.DataFrame(
            {
                "kod": category.code,
                "nazwa": category.name,
                "definicja": category.definition,
                "włączamy": "; ".join(category.include),
                "wykluczamy": "; ".join(category.exclude),
                "przykład +": category.positive[0].text,
                "przykład −": f"{category.negative[0].text} ({category.negative[0].why})",
            }
            for category in self.categories
        )

    def rules_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"reguła": rule.code, "treść": rule.text} for rule in self.rules)

    def to_markdown(self) -> str:
        """Render the annotation guide that annotators read."""
        lines = [
            f"# {self.title}: codebook v{self.version}",
            "",
            f"*{self.date.isoformat()} · {self.status}.*",
            "Ten plik jest generowany z `codebook/codebook.yaml` (`make codebook`); nie edytuj go ręcznie.",
            "",
            "## Konstrukt",
            "",
            self.construct_definition,
            "",
            "## Jednostki analizy",
            "",
            "| Platforma | Jednostka | Tekst | Uwagi |",
            "|---|---|---|---|",
            *(
                f"| {_cell(unit.platform)} | {_cell(unit.unit)} | {_cell(unit.text)} | {_cell(unit.note)} |"
                for unit in self.units
            ),
            "",
            "## Zmienne",
        ]
        for variable in self.variables:
            lines += [
                "",
                f"### `{variable.code}`: {variable.name}",
                "",
                f"Platformy: {', '.join(variable.platforms)}. Typ: {variable.type}.",
                "",
                f"**Pytanie:** {variable.question}",
            ]
            if variable.requires:
                lines += ["", f"**Warunek:** {variable.requires}"]
            if variable.derived:
                lines += ["", f"**Wyliczana** {variable.derived}."]
            if variable.values:
                lines += ["", *(f"- `{value}`: {meaning}" for value, meaning in variable.values.items())]

        lines += ["", "## Kategorie `source_types`"]
        for category in self.categories:
            lines += [
                "",
                f"### `{category.code}`: {category.name}",
                "",
                category.definition,
                "",
                "**Włączamy:**",
                *(f"- {item}" for item in category.include),
                "",
                "**Wykluczamy:**",
                *(f"- {item}" for item in category.exclude),
                "",
                "**Przykłady pozytywne:**",
                *(f"- *({example.platform})* {example.text}" for example in category.positive),
                "",
                "**Przykłady negatywne:**",
                *(
                    f"- *({example.platform})* {example.text} **Dlaczego nie:** {example.why}"
                    for example in category.negative
                ),
            ]

        lines += [
            "",
            "## Reguły rozstrzygania",
            "",
            *(f"- **{rule.code}.** {rule.text}" for rule in self.rules),
            "",
            "## Arkusz annotacji",
            "",
            "| Kolumna | Opis |",
            "|---|---|",
            *(f"| `{column.name}` | {_cell(column.description)} |" for column in self.annotation_columns),
            "",
            "## Historia zmian",
            "",
            *(
                f"- **{entry.version}** ({entry.date.isoformat()}): {entry.changes}"
                for entry in self.changelog
            ),
            "",
        ]
        return "\n".join(lines)


def _cell(text: str) -> str:
    """Make text safe for a single Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def load_codebook(path: Path = CODEBOOK_PATH) -> Codebook:
    with path.open(encoding="utf-8") as file:
        return Codebook.model_validate(yaml.safe_load(file))
