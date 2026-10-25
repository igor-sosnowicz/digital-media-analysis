"""Download the revision histories of the H2 v2 frame (articles and talk pages) into data/raw/wikipedia_v2/.

For every page of annotations/hypotheses_v2/h2_pages.csv and every namespace of
`hypotheses_v2.h2.namespaces`, the last revision before the baseline period and
every revision until the download time are kept as references and metadata
(wikipedia_history.revision_record), one gzipped JSON-lines file per page:
data/raw/wikipedia_v2/<namespace>/<article pageid>.jsonl.gz. Pages already
downloaded are skipped, so an interrupted run resumes; `--limit` downloads
only the first pages, to check the download before the full run. Needs the
committed preregistration v2. The full download reads every revision's text
(several GB over the network) and takes hours.
"""

import argparse
import json
from datetime import UTC, datetime

import httpx
import pandas as pd
from tqdm import tqdm

from digital_media_analysis.config_reader import get_hypotheses_v2
from digital_media_analysis.paths import HYPOTHESES_V2_DIR, RAW_WIKIPEDIA_V2_DIR
from digital_media_analysis.prereg import require_committed
from digital_media_analysis.wikipedia_frame import USER_AGENT, api_get
from digital_media_analysis.wikipedia_history import fetch_history, save_records

TALK_PREFIX = "Dyskusja:"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Download only the first N pages of the list.")
    args = parser.parse_args()
    commit = require_committed()
    settings = get_hypotheses_v2()["h2"]
    pages = pd.read_csv(HYPOTHESES_V2_DIR / "h2_pages.csv")
    if args.limit:
        pages = pages.head(args.limit)
    start = f"{settings['baseline_period'][0]}-01-01T00:00:00Z"
    end = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    api = f"https://{settings['wiki']}/w/api.php"
    log_path = RAW_WIKIPEDIA_V2_DIR / "fetch_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {"pages": {}}
    log.update({"commit": commit, "start": start, "api": api})
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120) as client:
        get = lambda params: api_get(client, api, params)  # noqa: E731
        for page in tqdm(pages.itertuples(index=False), total=len(pages), desc="Wikipedia histories"):
            for namespace in settings["namespaces"]:
                path = RAW_WIKIPEDIA_V2_DIR / str(namespace) / f"{page.pageid}.jsonl.gz"
                if path.exists():
                    continue
                title = page.title if namespace == 0 else TALK_PREFIX + page.title
                records = ({**record, "article": int(page.pageid), "group": page.group} for record in fetch_history(get, title, start, end))
                count = save_records(records, path)
                log["pages"][f"{namespace}/{page.pageid}"] = {"title": title, "revisions": count, "end": end}
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Histories in {RAW_WIKIPEDIA_V2_DIR} ({len(log['pages'])} page files)")


if __name__ == "__main__":
    main()
