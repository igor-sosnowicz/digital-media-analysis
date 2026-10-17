"""Draw the year-balanced gold-standard sample (pilot, dev, test) and save its manifest to `annotations/`."""

import argparse

from digital_media_analysis import gold


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing sample. Use only before annotation has started.",
    )
    args = parser.parse_args()

    reddit, wikipedia = gold.load_units()
    manifest, design = gold.draw_sample(reddit, wikipedia)
    gold.save_sample(manifest, design, force=args.force)

    for platform in ["reddit", "wikipedia"]:
        print(f"{platform}:\n{gold.year_summary(manifest, platform).to_string()}\n")
    for platform, allocation in design["allocation"].items():
        whole = ", ".join(map(str, allocation["whole_years"])) or "none"
        print(f"{platform}: {allocation['total']} units; years too small for an even share, drawn whole: {whole}")
    print(f"Manifest written to {gold.MANIFEST_PATH}")


if __name__ == "__main__":
    main()
