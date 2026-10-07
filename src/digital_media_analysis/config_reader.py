"""Read values from the project's config.yaml file."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = (Path(__file__).parent.parent).with_name("config.yaml").resolve()


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise TypeError(f"{CONFIG_PATH} must contain a YAML mapping.")

    return config


def get_config(key: str) -> Any:
    """Return a top-level config value by key."""
    config = _load_config()
    try:
        return config[key]
    except KeyError as exc:
        raise KeyError(f"Config key {key!r} not found in {CONFIG_PATH}.") from exc
