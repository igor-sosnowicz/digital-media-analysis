"""Render `codebook/codebook.yaml` into the annotator guide `codebook/codebook.md`."""

from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import CODEBOOK_PATH


def main() -> None:
    codebook = load_codebook()
    output_path = CODEBOOK_PATH.with_suffix(".md")
    output_path.write_text(codebook.to_markdown(), encoding="utf-8")
    print(f"Codebook v{codebook.version} written to {output_path}")


if __name__ == "__main__":
    main()
