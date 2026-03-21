"""
Fetch annual state tax collections from the Census Bureau State Tax API.

Endpoint pattern: https://api.census.gov/data/{year}/stax
Collects categories: individual income, corporate income, general sales,
selective sales, property, license, and severance taxes.

Output: data/processed/census_tax_collections.json
"""

import logging
import os
import sys

from scripts.config import (
    CENSUS_API_BASE,
    CENSUS_API_KEY,
    DEFAULT_YEAR,
    FIPS_TO_STATE,
    PROCESSED_DIR,
    STATE_FIPS,
    STATE_NAMES,
    YEAR_RANGE,
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

logger = setup_logging("pipeline.census_tax")

# Census STAX tax category codes
TAX_CATEGORIES = {
    "T01": "property_tax",
    "T09": "general_sales_tax",
    "T10": "alcoholic_beverage_tax",
    "T11": "amusement_tax",
    "T12": "insurance_premium_tax",
    "T13": "motor_fuel_tax",
    "T14": "pari_mutuel_tax",
    "T15": "public_utility_tax",
    "T16": "tobacco_tax",
    "T19": "other_selective_sales_tax",
    "T20": "alcoholic_beverage_license",
    "T21": "amusement_license",
    "T22": "corporation_license",
    "T23": "hunting_fishing_license",
    "T24": "motor_vehicle_license",
    "T25": "motor_vehicle_operator_license",
    "T27": "public_utility_license",
    "T28": "occupation_business_license",
    "T29": "other_license",
    "T40": "individual_income_tax",
    "T41": "corporate_income_tax",
    "T50": "death_gift_tax",
    "T51": "documentary_stamp_tax",
    "T53": "severance_tax",
    "T99": "other_tax",
}

# Aggregate groupings used for chart output
AGGREGATE_MAP = {
    "individual_income": ["T40"],
    "corporate_income": ["T41"],
    "general_sales": ["T09"],
    "selective_sales": ["T10", "T11", "T12", "T13", "T14", "T15", "T16", "T19"],
    "property": ["T01"],
    "license": ["T20", "T21", "T22", "T23", "T24", "T25", "T27", "T28", "T29"],
    "severance": ["T53"],
}


def _fetch_stax_year(year: int) -> list[dict] | None:
    """Fetch state tax collection data for a single year."""
    url = f"{CENSUS_API_BASE}/{year}/stax"
    params = {
        "get": "NAME,STAX,AMOUNT",
        "for": "state:*",
    }
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    cache_key = f"census_stax_{year}"
    data = cached_request(url, cache_key, params=params)
    if data is None:
        return None
    return data


def _parse_stax_response(raw: list[list[str]], year: int) -> dict:
    """
    Parse Census STAX API response into structured dict keyed by state abbrev.

    The API returns a list of lists where the first element is column headers.
    """
    if not raw or len(raw) < 2:
        logger.warning("Empty or malformed STAX response for year %d", year)
        return {}

    headers = [h.upper() for h in raw[0]]
    rows = raw[1:]

    name_idx = headers.index("NAME") if "NAME" in headers else None
    tax_idx = headers.index("STAX") if "STAX" in headers else None
    amt_idx = headers.index("AMOUNT") if "AMOUNT" in headers else None
    state_idx = headers.index("STATE") if "STATE" in headers else None

    if any(i is None for i in (tax_idx, amt_idx, state_idx)):
        logger.error("Missing expected columns in STAX response: %s", headers)
        return {}

    result: dict[str, dict] = {}
    for row in rows:
        fips = row[state_idx].zfill(2)
        abbr = FIPS_TO_STATE.get(fips)
        if abbr is None:
            continue

        tax_code = row[tax_idx]
        try:
            amount = float(row[amt_idx]) if row[amt_idx] else 0.0
        except (ValueError, TypeError):
            amount = 0.0

        if abbr not in result:
            result[abbr] = {"state": abbr, "name": STATE_NAMES.get(abbr, ""), "year": year}

        cat_name = TAX_CATEGORIES.get(tax_code, tax_code)
        result[abbr][cat_name] = amount

    return result


def _aggregate_categories(state_data: dict) -> dict:
    """Add aggregate totals (individual_income, general_sales, etc.) to each state."""
    for abbr, rec in state_data.items():
        for agg_name, codes in AGGREGATE_MAP.items():
            total = 0.0
            for code in codes:
                cat_name = TAX_CATEGORIES.get(code, code)
                total += rec.get(cat_name, 0.0)
            rec[f"{agg_name}_total"] = total
        # Grand total
        rec["total_tax_revenue"] = sum(
            rec.get(f"{agg}_total", 0.0) for agg in AGGREGATE_MAP
        )
    return state_data


def fetch_census_tax(year: int | None = None) -> dict:
    """
    Main entry point: fetch and process Census state tax collections.

    Returns a dict keyed by state abbreviation.
    """
    if not check_api_key("CENSUS_API_KEY", CENSUS_API_KEY):
        logger.error(
            "Census API key is required. Get one free at "
            "https://api.census.gov/data/key_signup.html and set CENSUS_API_KEY "
            "in your .env file."
        )
        return {}

    ensure_dirs()
    target_year = year or DEFAULT_YEAR

    logger.info("Fetching Census STAX data for year %d", target_year)
    raw = _fetch_stax_year(target_year)
    if raw is None:
        logger.error("Failed to retrieve Census STAX data for %d", target_year)
        return {}

    state_data = _parse_stax_response(raw, target_year)
    state_data = _aggregate_categories(state_data)

    # Data-quality checks
    check_state_coverage(state_data, "Census STAX")
    records = list(state_data.values())
    check_nulls(records, ["individual_income_total", "general_sales_total"], "Census STAX")

    # Save
    output_path = os.path.join(PROCESSED_DIR, "census_tax_collections.json")
    save_json(state_data, output_path)
    logger.info("Saved Census tax collections to %s", output_path)

    return state_data


if __name__ == "__main__":
    fetch_census_tax()
