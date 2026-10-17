from datetime import UTC, datetime

import httpx
import numpy as np
import pytest

from digital_media_analysis import reddit_archive

START = datetime(2020, 1, 1, tzinfo=UTC)
END = datetime(2021, 1, 1, tzinfo=UTC)


def archive(posts: list[dict], busy: int = 0) -> httpx.Client:
    """A fake archive with exclusive `after`/`before`, ascending pages and `busy` initial 422 answers."""
    state = {"busy": busy}

    def handler(request: httpx.Request) -> httpx.Response:
        if state["busy"]:
            state["busy"] -= 1
            return httpx.Response(422, json={"data": None, "error": "Timeout. Maybe slow down a bit"})
        params = request.url.params
        after, before = int(params["after"]), int(params["before"])
        window = sorted(
            (post for post in posts if after < post["created_utc"] < before), key=lambda post: post["created_utc"]
        )
        return httpx.Response(200, json={"data": window[: int(params["limit"])]})

    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(reddit_archive.time, "sleep", lambda seconds: None)


def test_paging_keeps_posts_that_share_a_timestamp_across_pages():
    base = int(START.timestamp())
    # 250 posts, five per second, so page boundaries fall inside a shared second.
    posts = [{"id": f"p{i}", "created_utc": base + i // 5} for i in range(250)]
    fetched = reddit_archive.fetch_window(archive(posts), "x", START, END)
    assert [post["id"] for post in fetched] == [post["id"] for post in posts]


def test_window_includes_start_and_excludes_end():
    posts = [
        {"id": "before", "created_utc": int(START.timestamp()) - 1},
        {"id": "first", "created_utc": int(START.timestamp())},
        {"id": "last", "created_utc": int(END.timestamp()) - 1},
        {"id": "after", "created_utc": int(END.timestamp())},
    ]
    client = archive(posts)
    assert [post["id"] for post in reddit_archive.fetch_window(client, "x", START, END)] == ["first", "last"]


def test_busy_archive_is_retried():
    posts = [{"id": "a", "created_utc": int(START.timestamp()) + 10}]
    assert len(reddit_archive.fetch_window(archive(posts, busy=2), "x", START, END)) == 1
    with pytest.raises(httpx.HTTPStatusError):
        reddit_archive.fetch_window(archive(posts, busy=reddit_archive.MAX_ATTEMPTS), "x", START, END)


def test_post_row_keeps_removal_marker():
    row = reddit_archive.post_row({"id": "a", "created_utc": 0, "selftext": "[removed]", "removed_by_category": "moderator"})
    assert row["created_at_utc"] == "1970-01-01T00:00:00+00:00"
    assert (row["text"], row["removed_by_category"]) == ("[removed]", "moderator")
    assert reddit_archive.post_row({"id": "b"})["removed_by_category"] == ""
    assert reddit_archive.post_row({"id": "c", "day_weight": 31.0})["day_weight"] == 31.0


def test_draw_days_takes_distinct_days_of_every_month_with_their_weights():
    days = reddit_archive.draw_days(2008, 2, np.random.default_rng(0))
    assert len(days) == 24
    assert len({day for day, _ in days}) == 24
    assert all(day.year == 2008 for day, _ in days)
    assert {day.month for day, _ in days} == set(range(1, 13))
    weights = {day.month: weight for day, weight in days}
    assert (weights[1], weights[2], weights[4]) == (15.5, 14.5, 15.0)  # 2008 is a leap year
    assert reddit_archive.draw_days(2008, 2, np.random.default_rng(0)) == days
