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

from scripts.config import RAW_DIR, PROCESSED_DIR, REFERENCE_DIR, SITE_DIR, CACHE_DIR


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
    for d in (RAW_DIR, PROCESSED_DIR, REFERENCE_DIR, SITE_DIR, CACHE_DIR):
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


# ---------------------------------------------------------------------------
# Profile schema validation
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = ["state", "abbreviation", "last_updated"]

_TAX_STRUCTURE_KEYS = [
    "income_tax_type", "income_tax_brackets", "sales_tax_rate",
    "local_sales_tax", "corporate_tax_rate", "property_tax_admin",
    "estate_tax", "notable_credits",
]

_ECONOMIC_CONTEXT_KEYS = [
    "median_household_income", "per_capita_income", "gdp_per_capita",
    "population", "unemployment_rate",
]

_COMPETITIVENESS_KEYS = [
    "overall_rank", "corporate_rank", "individual_income_rank",
    "sales_tax_rank", "property_tax_rank", "unemployment_insurance_rank",
]


def validate_profile_schema(profile: dict, strict: bool = False) -> list[str]:
    """
    Validate a generated state profile against the expected schema.

    Parameters
    ----------
    profile : dict
        The state profile to validate.
    strict : bool
        If True, require all fields to be non-null (use for MN/WI).
        If False, allow nulls for partially-populated states.

    Returns
    -------
    list[str]
        List of error/warning strings. Empty list means valid.
    """
    errors = []

    # Required top-level keys
    for key in _REQUIRED_KEYS:
        if key not in profile:
            errors.append(f"Missing required key: {key}")
        elif profile[key] is None:
            errors.append(f"Required key '{key}' is null")

    # tax_structure
    ts = profile.get("tax_structure")
    if ts is None:
        if strict:
            errors.append("tax_structure is null (strict mode)")
    elif not isinstance(ts, dict):
        errors.append("tax_structure is not a dict")
    elif strict:
        for k in _TAX_STRUCTURE_KEYS:
            if ts.get(k) is None:
                errors.append(f"tax_structure.{k} is null (strict mode)")

    # revenue_composition
    rc = profile.get("revenue_composition")
    if rc is None:
        if strict:
            errors.append("revenue_composition is null (strict mode)")
    elif not isinstance(rc, dict):
        errors.append("revenue_composition is not a dict")
    else:
        labels = rc.get("labels")
        datasets = rc.get("datasets")
        if not isinstance(labels, list) or not labels:
            errors.append("revenue_composition.labels is missing or empty")
        elif not all(isinstance(l, str) for l in labels):
            errors.append("revenue_composition.labels contains non-string elements")
        if not isinstance(datasets, list) or not datasets:
            errors.append("revenue_composition.datasets is missing or empty")
        else:
            ds = datasets[0]
            if not isinstance(ds, dict):
                errors.append("revenue_composition.datasets[0] is not a dict")
            else:
                data = ds.get("data")
                if not isinstance(data, list):
                    errors.append("revenue_composition.datasets[0].data is not a list")
                elif not all(isinstance(v, (int, float)) for v in data):
                    errors.append("revenue_composition.datasets[0].data contains non-numeric values")

    # effective_rates_by_quintile
    er = profile.get("effective_rates_by_quintile")
    if er is None:
        if strict:
            errors.append("effective_rates_by_quintile is null (strict mode)")
    elif not isinstance(er, dict):
        errors.append("effective_rates_by_quintile is not a dict")
    else:
        labels = er.get("labels")
        datasets = er.get("datasets")
        is_partial = er.get("_partial", False)
        expected_len = 2 if is_partial else 7
        if not isinstance(labels, list) or len(labels) != expected_len:
            errors.append(f"effective_rates_by_quintile.labels should have {expected_len} items")
        if not isinstance(datasets, list) or len(datasets) < 1:
            errors.append("effective_rates_by_quintile.datasets is missing or empty")
        else:
            for i, ds in enumerate(datasets):
                if not isinstance(ds, dict):
                    errors.append(f"effective_rates_by_quintile.datasets[{i}] is not a dict")
                    continue
                if "label" not in ds:
                    errors.append(f"effective_rates_by_quintile.datasets[{i}] missing 'label'")
                data = ds.get("data")
                if not isinstance(data, list) or len(data) != expected_len:
                    errors.append(f"effective_rates_by_quintile.datasets[{i}].data should have {expected_len} items")
                if "backgroundColor" not in ds:
                    errors.append(f"effective_rates_by_quintile.datasets[{i}] missing 'backgroundColor'")

    # economic_context
    ec = profile.get("economic_context")
    if ec is None:
        if strict:
            errors.append("economic_context is null (strict mode)")
    elif not isinstance(ec, dict):
        errors.append("economic_context is not a dict")
    elif strict:
        for k in _ECONOMIC_CONTEXT_KEYS:
            if ec.get(k) is None:
                errors.append(f"economic_context.{k} is null (strict mode)")

    # competitiveness_index
    ci = profile.get("competitiveness_index")
    if ci is None:
        if strict:
            errors.append("competitiveness_index is null (strict mode)")
    elif not isinstance(ci, dict):
        errors.append("competitiveness_index is not a dict")
    else:
        for k in _COMPETITIVENESS_KEYS:
            val = ci.get(k)
            if val is None:
                if strict:
                    errors.append(f"competitiveness_index.{k} is null (strict mode)")
            elif not isinstance(val, int) or val < 1 or val > 51:
                errors.append(f"competitiveness_index.{k} = {val} is not a valid rank (1-51)")

    # key_facts
    kf = profile.get("key_facts")
    if kf is None:
        if strict:
            errors.append("key_facts is null (strict mode)")
    elif not isinstance(kf, dict):
        errors.append("key_facts is not a dict")

    # migration (optional — only validate structure if present)
    mig = profile.get("migration")
    if mig is not None:
        if not isinstance(mig, dict):
            errors.append("migration is not a dict")

    # property_tax (optional — only validate structure if present)
    pt = profile.get("property_tax")
    if pt is not None:
        if not isinstance(pt, dict):
            errors.append("property_tax is not a dict")

    return errors
