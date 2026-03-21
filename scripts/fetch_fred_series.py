"""
Fetch state-level economic series from the FRED (Federal Reserve) API.

Pulls unemployment rate and median household income series for each state.

Output: data/processed/fred_economic_series.json
"""

import logging
import os
import sys

from scripts.config import (
    FRED_API_BASE,
    FRED_API_KEY,
    PROCESSED_DIR,
    STATE_FIPS,
    STATE_NAMES,
    check_api_key,
)
from scripts.utils import (
    cached_request,
    check_nulls,
    check_state_coverage,
    ensure_dirs,
    save_json,
    setup_logging,
)

logger = setup_logging("pipeline.fred_series")

# FRED series ID patterns by state abbreviation.
# Unemployment rate: {ABBR}UR  (e.g., ALUR, AKUR)
# Median household income: MEHOINUS{FIPS}A646NCEN  (e.g., MEHOINUSAL01A646NCEN)
# Note: some series use slightly different naming; we handle common patterns.

def _unemployment_series_id(abbr: str) -> str:
    """Return the FRED series ID for a state's unemployment rate."""
    return f"{abbr}UR"


def _median_income_series_id(abbr: str, fips: str) -> str:
    """Return the FRED series ID for a state's median household income."""
    return f"MEHOINUS{abbr}A672N"


def _fetch_series_latest(series_id: str) -> dict | None:
    """
    Fetch the most recent observation for a FRED series.

    Returns a dict with 'date' and 'value' keys, or None on failure.
    """
    url = f"{FRED_API_BASE}/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": "5",
    }
    cache_key = f"fred_{series_id}"
    data = cached_request(url, cache_key, params=params)
    if data is None:
        return None

    try:
        observations = data.get("observations", [])
        # Find the most recent non-missing value
        for obs in observations:
            val = obs.get("value", ".")
            if val != ".":
                return {"date": obs["date"], "value": float(val)}
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Could not parse FRED series %s: %s", series_id, exc)

    return None


def fetch_fred_series() -> dict:
    """
    Main entry point: fetch FRED state-level economic series.

    Returns a dict keyed by state abbreviation.
    """
    if not check_api_key("FRED_API_KEY", FRED_API_KEY):
        logger.error(
            "FRED API key is required. Register at "
            "https://fred.stlouisfed.org/docs/api/api_key.html and set "
            "FRED_API_KEY in your .env file."
        )
        return {}

    ensure_dirs()
    logger.info("Fetching FRED state-level economic series")

    state_data = {}
    for abbr, fips in sorted(STATE_FIPS.items()):
        rec = {
            "state": abbr,
            "name": STATE_NAMES.get(abbr, ""),
        }

        # Unemployment rate
        ur_id = _unemployment_series_id(abbr)
        ur = _fetch_series_latest(ur_id)
        if ur:
            rec["unemployment_rate"] = ur["value"]
            rec["unemployment_rate_date"] = ur["date"]
        else:
            rec["unemployment_rate"] = None
            rec["unemployment_rate_date"] = None
            logger.debug("No unemployment data for %s (series %s)", abbr, ur_id)

        # Median household income
        mi_id = _median_income_series_id(abbr, fips)
        mi = _fetch_series_latest(mi_id)
        if mi:
            rec["median_household_income"] = mi["value"]
            rec["median_household_income_date"] = mi["date"]
        else:
            rec["median_household_income"] = None
            rec["median_household_income_date"] = None
            logger.debug("No median income data for %s (series %s)", abbr, mi_id)

        state_data[abbr] = rec

    # Quality checks
    check_state_coverage(state_data, "FRED Series")
    check_nulls(
        list(state_data.values()),
        ["unemployment_rate", "median_household_income"],
        "FRED Series",
    )

    # Save
    output_path = os.path.join(PROCESSED_DIR, "fred_economic_series.json")
    save_json(state_data, output_path)
    logger.info("Saved FRED economic series to %s", output_path)

    return state_data


if __name__ == "__main__":
    fetch_fred_series()
