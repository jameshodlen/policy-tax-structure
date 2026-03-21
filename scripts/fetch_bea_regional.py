"""
Fetch regional economic data from the Bureau of Economic Analysis (BEA) API.

Retrieves state personal income (SAINC), GDP by state (SAGDP), and
regional price parities.

Output: data/processed/bea_economic_context.json
"""

import logging
import os
import sys

from scripts.config import (
    BEA_API_BASE,
    BEA_API_KEY,
    DEFAULT_YEAR,
    FIPS_TO_STATE,
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

logger = setup_logging("pipeline.bea_regional")


def _bea_request(dataset: str, table: str, line_code: str, year: str) -> dict | None:
    """Execute a single BEA API request and return the parsed JSON."""
    params = {
        "UserID": BEA_API_KEY,
        "method": "GetData",
        "datasetname": dataset,
        "TableName": table,
        "LineCode": line_code,
        "Year": year,
        "GeoFips": "STATE",
        "ResultFormat": "JSON",
    }
    cache_key = f"bea_{dataset}_{table}_{line_code}_{year}"
    url = f"{BEA_API_BASE}/data"
    data = cached_request(url, cache_key, params=params)
    return data


def _extract_state_values(bea_json: dict) -> dict[str, float]:
    """
    Extract state-level values from a BEA API response.

    Returns a dict mapping state abbreviation to numeric value.
    """
    result = {}
    try:
        records = bea_json["BEAAPI"]["Results"]["Data"]
    except (KeyError, TypeError):
        logger.warning("Unexpected BEA response structure")
        return result

    for rec in records:
        fips = rec.get("GeoFips", "").strip()
        # BEA uses 5-digit FIPS with trailing zeros for states (e.g., "01000")
        if len(fips) == 5:
            state_fips = fips[:2]
        elif len(fips) == 2:
            state_fips = fips
        else:
            continue

        abbr = FIPS_TO_STATE.get(state_fips)
        if abbr is None:
            continue

        raw_val = rec.get("DataValue", "")
        try:
            value = float(str(raw_val).replace(",", ""))
        except (ValueError, TypeError):
            value = None

        result[abbr] = value

    return result


def _fetch_personal_income(year: int) -> dict[str, float]:
    """Fetch state personal income (SAINC1, line 1 = total personal income)."""
    data = _bea_request("Regional", "SAINC1", "1", str(year))
    if data is None:
        return {}
    return _extract_state_values(data)


def _fetch_per_capita_income(year: int) -> dict[str, float]:
    """Fetch per-capita personal income (SAINC1, line 3)."""
    data = _bea_request("Regional", "SAINC1", "3", str(year))
    if data is None:
        return {}
    return _extract_state_values(data)


def _fetch_gdp_by_state(year: int) -> dict[str, float]:
    """Fetch real GDP by state (SAGDP9N, line 1 = all industry total)."""
    data = _bea_request("Regional", "SAGDP9N", "1", str(year))
    if data is None:
        return {}
    return _extract_state_values(data)


def _fetch_regional_price_parities(year: int) -> dict[str, float]:
    """Fetch regional price parities (SARPP, line 1 = all items)."""
    data = _bea_request("Regional", "SARPP", "1", str(year))
    if data is None:
        return {}
    return _extract_state_values(data)


def fetch_bea_regional(year: int | None = None) -> dict:
    """
    Main entry point: fetch BEA regional economic data for all states.

    Returns a dict keyed by state abbreviation containing personal income,
    per-capita income, GDP, and regional price parities.
    """
    if not check_api_key("BEA_API_KEY", BEA_API_KEY):
        logger.error(
            "BEA API key is required. Register at "
            "https://apps.bea.gov/api/signup/ and set BEA_API_KEY in your .env file."
        )
        return {}

    ensure_dirs()
    target_year = year or DEFAULT_YEAR

    logger.info("Fetching BEA regional data for year %d", target_year)

    personal_income = _fetch_personal_income(target_year)
    per_capita_income = _fetch_per_capita_income(target_year)
    gdp = _fetch_gdp_by_state(target_year)
    rpp = _fetch_regional_price_parities(target_year)

    # Merge into per-state records
    all_abbrs = set(STATE_FIPS.keys())
    state_data = {}
    for abbr in sorted(all_abbrs):
        state_data[abbr] = {
            "state": abbr,
            "name": STATE_NAMES.get(abbr, ""),
            "year": target_year,
            "personal_income": personal_income.get(abbr),
            "per_capita_income": per_capita_income.get(abbr),
            "gdp": gdp.get(abbr),
            "regional_price_parity": rpp.get(abbr),
        }

    # Quality checks
    check_state_coverage(state_data, "BEA Regional")
    check_nulls(
        list(state_data.values()),
        ["personal_income", "per_capita_income", "gdp"],
        "BEA Regional",
    )

    # Save
    output_path = os.path.join(PROCESSED_DIR, "bea_economic_context.json")
    save_json(state_data, output_path)
    logger.info("Saved BEA economic context to %s", output_path)

    return state_data


if __name__ == "__main__":
    fetch_bea_regional()
