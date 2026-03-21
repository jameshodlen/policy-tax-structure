"""
Shared utilities for the tax structure data pipeline.

Provides caching, directory management, JSON I/O, and logging setup.
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from scripts.config import RAW_DIR, PROCESSED_DIR, SITE_DIR, CACHE_DIR


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(name: str = "pipeline", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with timestamped console output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def ensure_dirs() -> None:
    """Create all required data directories if they do not exist."""
    for d in (RAW_DIR, PROCESSED_DIR, SITE_DIR, CACHE_DIR):
        os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def save_json(data: Any, path: str) -> None:
    """Write *data* as pretty-printed JSON to *path*, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_json(path: str) -> Any:
    """Read and return parsed JSON from *path*. Returns None if missing."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Cached HTTP requests
# ---------------------------------------------------------------------------

def _cache_path(cache_key: str) -> str:
    """Return the filesystem path for a given cache key."""
    safe = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
    # Keep the key human-readable but filesystem-safe
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in cache_key)[:80]
    return os.path.join(CACHE_DIR, f"{slug}__{safe}.json")


def _cache_is_fresh(path: str, max_age_hours: float) -> bool:
    """Return True if the cached file exists and is younger than *max_age_hours*."""
    if not os.path.exists(path):
        return False
    mtime = os.path.getmtime(path)
    age_hours = (time.time() - mtime) / 3600.0
    return age_hours < max_age_hours


def cached_request(
    url: str,
    cache_key: str,
    max_age_hours: float = 24.0,
    params: Optional[dict] = None,
    timeout: int = 60,
) -> Optional[Any]:
    """
    Perform an HTTP GET and return the parsed JSON response.

    Results are cached locally under ``data/raw/cache/`` so repeated runs
    within *max_age_hours* hit the filesystem instead of the network.

    Returns ``None`` on request failure (after logging the error).
    """
    logger = logging.getLogger("pipeline.http")
    ensure_dirs()

    cp = _cache_path(cache_key)
    if _cache_is_fresh(cp, max_age_hours):
        logger.debug("Cache hit: %s", cache_key)
        return load_json(cp)

    logger.info("Fetching %s", url[:120])
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        save_json(data, cp)
        return data
    except requests.RequestException as exc:
        logger.error("Request failed for %s: %s", cache_key, exc)
        # Fall back to stale cache if available
        if os.path.exists(cp):
            logger.warning("Returning stale cache for %s", cache_key)
            return load_json(cp)
        return None


# ---------------------------------------------------------------------------
# Data-quality helpers
# ---------------------------------------------------------------------------

def check_state_coverage(data: dict, label: str, expected: int = 51) -> None:
    """Log a warning if the number of state entries differs from expected."""
    logger = logging.getLogger("pipeline.quality")
    count = len(data)
    if count < expected:
        logger.warning(
            "%s: only %d/%d states present — %d missing",
            label, count, expected, expected - count,
        )
    else:
        logger.info("%s: %d states present (expected %d)", label, count, expected)


def check_nulls(records: list[dict], fields: list[str], label: str) -> int:
    """Count and log null/None values across *fields* in a list of dicts."""
    logger = logging.getLogger("pipeline.quality")
    null_count = 0
    for rec in records:
        for f in fields:
            if rec.get(f) is None:
                null_count += 1
    if null_count:
        logger.warning("%s: %d null values across fields %s", label, null_count, fields)
    return null_count
