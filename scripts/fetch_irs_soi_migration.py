"""
Fetch IRS Statistics of Income (SOI) state-to-state migration data.

The IRS publishes migration flow data as downloadable CSV files (no API).
This script downloads the state-to-state inflow/outflow files, parses them,
and produces structured JSON with per-state migration aggregates.

When CSV downloads are unavailable, the script falls back to manually-maintained
reference data at data/reference/irs_soi_migration.json.

Output: data/processed/irs_soi_migration.json
"""

import csv
import io
import logging
import os
import sys
from typing import Any, Optional

import requests

from scripts.config import (
    FIPS_TO_STATE,
    PROCESSED_DIR,
    RAW_DIR,
    STATE_FIPS,
    STATE_NAMES,
)
from scripts.utils import (
    ensure_dirs,
    load_json,
    save_json,
    setup_logging,
    cached_request,
)

logger = setup_logging("pipeline.irs_soi_migration")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IRS_SOI_URL = "https://www.irs.gov/statistics/soi-tax-stats-migration-data"

# Known download URLs for recent state-to-state migration CSV files.
# The IRS periodically updates these; add new years as they become available.
KNOWN_CSV_URLS: dict[int, dict[str, str]] = {
    2021: {
        "inflow": "https://www.irs.gov/pub/irs-soi/stateinflow2021.csv",
        "outflow": "https://www.irs.gov/pub/irs-soi/stateoutflow2021.csv",
    },
    2022: {
        "inflow": "https://www.irs.gov/pub/irs-soi/stateinflow2122.csv",
        "outflow": "https://www.irs.gov/pub/irs-soi/stateoutflow2122.csv",
    },
}

DEFAULT_TAX_YEAR = 2022

# Cache directory for raw IRS SOI downloads
SOI_RAW_DIR = os.path.join(RAW_DIR, "irs_soi")

# Reference data fallback path
REFERENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "reference", "irs_soi_migration.json",
)

# Output path
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "irs_soi_migration.json")

# Threshold for data-quality warning: net AGI exceeding this fraction of a
# rough per-state personal income estimate flags unusually large migration.
NET_AGI_WARNING_FRACTION = 0.05

# Rough US personal income divided by 51 jurisdictions (in thousands of $).
# Used only for sanity-check warnings — not for calculations.
APPROX_PER_STATE_PERSONAL_INCOME_K = 200_000_000  # ~$200B in thousands


# ---------------------------------------------------------------------------
# CSV download helpers
# ---------------------------------------------------------------------------

def _download_csv(url: str, cache_file: str) -> Optional[str]:
    """
    Download a CSV file from *url*, cache it at *cache_file*, and return its
    text content.  Returns None on failure.  If a cached copy exists and the
    download fails, the cached copy is returned instead.
    """
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    try:
        logger.info("Downloading %s", url[:120])
        resp = requests.get(url, timeout=90)
        resp.raise_for_status()
        text = resp.text
        with open(cache_file, "w", encoding="utf-8") as fh:
            fh.write(text)
        logger.info("Cached CSV to %s", cache_file)
        return text
    except requests.RequestException as exc:
        logger.error("Download failed for %s: %s", url, exc)
        if os.path.exists(cache_file):
            logger.warning("Using previously cached file %s", cache_file)
            with open(cache_file, "r", encoding="utf-8") as fh:
                return fh.read()
        return None


def _download_migration_csvs(tax_year: int) -> tuple[Optional[str], Optional[str]]:
    """
    Attempt to download inflow and outflow CSVs for *tax_year*.

    Returns (inflow_text, outflow_text).  Either or both may be None.
    """
    urls = KNOWN_CSV_URLS.get(tax_year)
    if urls is None:
        logger.warning(
            "No known CSV URLs for tax year %d. Available years: %s",
            tax_year, sorted(KNOWN_CSV_URLS.keys()),
        )
        return None, None

    inflow_cache = os.path.join(SOI_RAW_DIR, f"stateinflow{tax_year}.csv")
    outflow_cache = os.path.join(SOI_RAW_DIR, f"stateoutflow{tax_year}.csv")

    inflow_text = _download_csv(urls["inflow"], inflow_cache)
    outflow_text = _download_csv(urls["outflow"], outflow_cache)

    return inflow_text, outflow_text


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def _normalize_header(header: str) -> str:
    """Lowercase and strip whitespace from a CSV header name."""
    return header.strip().lower()


def _parse_flow_csv(csv_text: str, flow_type: str) -> list[dict]:
    """
    Parse a state-to-state migration CSV into a list of flow records.

    Parameters
    ----------
    csv_text : str
        Raw CSV text.
    flow_type : str
        Either ``"inflow"`` or ``"outflow"``.

    Returns
    -------
    list[dict]
        Each dict has keys: origin_fips, dest_fips, origin_state, dest_state,
        returns, agi.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    # Normalize headers
    reader.fieldnames = [_normalize_header(h) for h in reader.fieldnames]

    records: list[dict] = []
    for row in reader:
        try:
            y1_fips = str(row.get("y1_statefips", "")).strip().zfill(2)
            y2_fips = str(row.get("y2_statefips", "")).strip().zfill(2)

            # Skip aggregate/non-state rows (FIPS 96, 97, 98 are totals)
            if y1_fips not in FIPS_TO_STATE or y2_fips not in FIPS_TO_STATE:
                continue

            # Skip same-state rows
            if y1_fips == y2_fips:
                continue

            n1_raw = row.get("n1", "0")
            n2_raw = row.get("n2", "0")
            agi_raw = row.get("agi", "0")

            # Clean numeric values: remove commas, handle 'd' (suppressed data)
            def _to_float(val: str) -> Optional[float]:
                val = val.strip().replace(",", "")
                if not val or val.lower() == "d" or val == "-1":
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None

            returns = _to_float(n1_raw)
            agi = _to_float(agi_raw)

            origin_abbr = FIPS_TO_STATE[y1_fips]
            dest_abbr = FIPS_TO_STATE[y2_fips]

            records.append({
                "origin_fips": y1_fips,
                "dest_fips": y2_fips,
                "origin_state": origin_abbr,
                "dest_state": dest_abbr,
                "returns": returns,
                "agi": agi,
            })
        except (KeyError, ValueError) as exc:
            logger.debug("Skipping malformed row: %s — %s", row, exc)
            continue

    logger.info("Parsed %d %s flow records", len(records), flow_type)
    return records


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _empty_state_record() -> dict:
    """Return a blank state migration record with null values."""
    return {
        "total_inflow_returns": None,
        "total_inflow_agi": None,
        "total_outflow_returns": None,
        "total_outflow_agi": None,
        "net_returns": None,
        "net_agi": None,
        "top_inflows": [],
        "top_outflows": [],
    }


def _aggregate_flows(
    inflow_records: list[dict],
    outflow_records: list[dict],
) -> dict[str, dict]:
    """
    Aggregate per-state-pair flow records into per-state summaries.

    Inflow records describe who moved *into* a destination state.
    Outflow records describe who moved *out of* an origin state.

    Returns a dict keyed by state abbreviation.
    """
    states: dict[str, dict] = {}

    # Initialize all states
    for abbr in STATE_FIPS:
        states[abbr] = _empty_state_record()

    # --- Process inflows: for each record, the *destination* state gains ----
    inflow_by_dest: dict[str, list[dict]] = {}
    for rec in inflow_records:
        dest = rec["dest_state"]
        inflow_by_dest.setdefault(dest, []).append(rec)

    for dest, recs in inflow_by_dest.items():
        if dest not in states:
            continue
        total_returns = 0.0
        total_agi = 0.0
        valid = False
        for r in recs:
            if r["returns"] is not None:
                total_returns += r["returns"]
                valid = True
            if r["agi"] is not None:
                total_agi += r["agi"]
                valid = True
        if valid:
            states[dest]["total_inflow_returns"] = total_returns
            states[dest]["total_inflow_agi"] = total_agi

        # Top 5 origin states by returns
        ranked = sorted(
            [r for r in recs if r["returns"] is not None],
            key=lambda x: x["returns"],
            reverse=True,
        )[:5]
        states[dest]["top_inflows"] = [
            {
                "state": r["origin_state"],
                "returns": r["returns"],
                "agi": r["agi"],
            }
            for r in ranked
        ]

    # --- Process outflows: for each record, the *origin* state loses -------
    outflow_by_origin: dict[str, list[dict]] = {}
    for rec in outflow_records:
        origin = rec["origin_state"]
        outflow_by_origin.setdefault(origin, []).append(rec)

    for origin, recs in outflow_by_origin.items():
        if origin not in states:
            continue
        total_returns = 0.0
        total_agi = 0.0
        valid = False
        for r in recs:
            if r["returns"] is not None:
                total_returns += r["returns"]
                valid = True
            if r["agi"] is not None:
                total_agi += r["agi"]
                valid = True
        if valid:
            states[origin]["total_outflow_returns"] = total_returns
            states[origin]["total_outflow_agi"] = total_agi

        # Top 5 destination states by returns
        ranked = sorted(
            [r for r in recs if r["returns"] is not None],
            key=lambda x: x["returns"],
            reverse=True,
        )[:5]
        states[origin]["top_outflows"] = [
            {
                "state": r["dest_state"],
                "returns": r["returns"],
                "agi": r["agi"],
            }
            for r in ranked
        ]

    # --- Compute net values ------------------------------------------------
    for abbr, rec in states.items():
        inflow_r = rec["total_inflow_returns"]
        outflow_r = rec["total_outflow_returns"]
        if inflow_r is not None and outflow_r is not None:
            rec["net_returns"] = inflow_r - outflow_r
        inflow_a = rec["total_inflow_agi"]
        outflow_a = rec["total_outflow_agi"]
        if inflow_a is not None and outflow_a is not None:
            rec["net_agi"] = inflow_a - outflow_a

    return states


# ---------------------------------------------------------------------------
# Data-quality checks
# ---------------------------------------------------------------------------

def _run_quality_checks(states: dict[str, dict]) -> None:
    """Log warnings for common data-quality issues."""
    missing_count = 0
    for abbr, rec in states.items():
        if rec["total_inflow_returns"] is None and rec["total_outflow_returns"] is None:
            missing_count += 1
            logger.debug("No migration data for %s", abbr)

    if missing_count:
        logger.warning(
            "%d/%d states have no migration data",
            missing_count, len(states),
        )

    # Check for unusually large net AGI
    for abbr, rec in states.items():
        net_agi = rec.get("net_agi")
        if net_agi is not None and abs(net_agi) > APPROX_PER_STATE_PERSONAL_INCOME_K * NET_AGI_WARNING_FRACTION:
            logger.warning(
                "%s has unusually large net AGI migration: %,.0f "
                "(exceeds %.0f%% of approx per-state personal income)",
                abbr, net_agi, NET_AGI_WARNING_FRACTION * 100,
            )

    # National consistency check: total inflow should roughly equal total outflow
    total_inflow = sum(
        rec["total_inflow_returns"]
        for rec in states.values()
        if rec["total_inflow_returns"] is not None
    )
    total_outflow = sum(
        rec["total_outflow_returns"]
        for rec in states.values()
        if rec["total_outflow_returns"] is not None
    )
    if total_inflow > 0 and total_outflow > 0:
        ratio = total_inflow / total_outflow
        if abs(ratio - 1.0) > 0.05:
            logger.warning(
                "National inflow/outflow mismatch: inflow=%,.0f, outflow=%,.0f, "
                "ratio=%.3f (expected ~1.0)",
                total_inflow, total_outflow, ratio,
            )
        else:
            logger.info(
                "National totals consistent: inflow=%,.0f, outflow=%,.0f, ratio=%.3f",
                total_inflow, total_outflow, ratio,
            )


# ---------------------------------------------------------------------------
# Reference-data fallback
# ---------------------------------------------------------------------------

def _load_reference_data() -> Optional[dict]:
    """
    Load manually-maintained reference data as a fallback when live CSV
    downloads are unavailable.

    Returns the full output dict (with _metadata and states) or None.
    """
    ref = load_json(REFERENCE_PATH)
    if ref is None:
        logger.warning("No reference data found at %s", REFERENCE_PATH)
        return None
    logger.info("Loaded reference migration data from %s", REFERENCE_PATH)
    return ref


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def fetch_irs_soi_migration(tax_year: int = DEFAULT_TAX_YEAR) -> dict:
    """
    Fetch and process IRS SOI state-to-state migration data.

    Attempts to download CSV files for the given tax year. If downloads fail,
    falls back to reference data. Returns the structured output dict.

    Parameters
    ----------
    tax_year : int
        The filing year for migration data (default 2022).

    Returns
    -------
    dict
        Output with ``_metadata`` and ``states`` keys.
    """
    ensure_dirs()
    os.makedirs(SOI_RAW_DIR, exist_ok=True)

    output = {
        "_metadata": {
            "source": "IRS Statistics of Income, Migration Data",
            "tax_year": tax_year,
            "url": IRS_SOI_URL,
        },
        "states": {},
    }

    # Attempt live CSV download
    logger.info("Attempting to download IRS SOI migration CSVs for tax year %d", tax_year)
    inflow_text, outflow_text = _download_migration_csvs(tax_year)

    if inflow_text is not None and outflow_text is not None:
        logger.info("Parsing downloaded CSV data")
        inflow_records = _parse_flow_csv(inflow_text, "inflow")
        outflow_records = _parse_flow_csv(outflow_text, "outflow")

        if inflow_records or outflow_records:
            states = _aggregate_flows(inflow_records, outflow_records)
            _run_quality_checks(states)
            output["states"] = states
            output["_metadata"]["data_source"] = "live_csv"
            save_json(output, OUTPUT_PATH)
            logger.info("Saved IRS SOI migration data to %s", OUTPUT_PATH)
            return output
        else:
            logger.warning("CSV download succeeded but parsing yielded no records")

    # Fallback to reference data
    logger.info("Falling back to reference data")
    ref = _load_reference_data()
    if ref is not None:
        # Merge reference data into output, preserving our metadata
        ref_states = ref.get("states", {})
        if ref_states:
            output["states"] = ref_states
            output["_metadata"]["data_source"] = "reference"
            if "_metadata" in ref and "tax_year" in ref["_metadata"]:
                output["_metadata"]["tax_year"] = ref["_metadata"]["tax_year"]
            save_json(output, OUTPUT_PATH)
            logger.info("Saved reference-based migration data to %s", OUTPUT_PATH)
            return output

    # No data available — save skeleton output
    logger.warning("No migration data available. Saving empty skeleton.")
    for abbr in STATE_FIPS:
        output["states"][abbr] = _empty_state_record()
    output["_metadata"]["data_source"] = "none"
    save_json(output, OUTPUT_PATH)
    logger.info("Saved empty skeleton to %s", OUTPUT_PATH)
    return output


if __name__ == "__main__":
    fetch_irs_soi_migration()
