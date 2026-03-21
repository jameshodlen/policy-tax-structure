"""
Fetch federal fiscal transfer data from the Treasury Fiscal Data API.

Retrieves federal grants to state governments and calculates federal
dependency ratios (federal grants as share of state revenue).

The Treasury Fiscal Data API is open and does not require an API key.

Output: data/processed/treasury_federal_transfers.json
"""

import logging
import os
import sys

from scripts.config import (
    TREASURY_API_BASE,
    PROCESSED_DIR,
    STATE_FIPS,
    STATE_NAMES,
    DEFAULT_YEAR,
)
from scripts.utils import (
    cached_request,
    check_nulls,
    check_state_coverage,
    ensure_dirs,
    load_json,
    save_json,
    setup_logging,
)

logger = setup_logging("pipeline.treasury_fiscal")

# Treasury Fiscal Data endpoint for federal grants to state governments
# Using the Monthly Treasury Statement (MTS) dataset for grants data
GRANTS_ENDPOINT = f"{TREASURY_API_BASE}/v1/accounting/mts/receipts_by_source_category"

# Federal Aid to State and Local Governments endpoint
FEDERAL_AID_ENDPOINT = (
    f"{TREASURY_API_BASE}/v2/revenue/federal-grants-to-state-and-local-governments"
)


def _fetch_federal_grants(fiscal_year: int) -> list[dict]:
    """
    Fetch federal grant data from Treasury Fiscal Data API.

    Returns a list of records with state-level grant amounts.
    """
    # Try the grants-to-states endpoint
    url = f"{TREASURY_API_BASE}/v1/accounting/mts/federal_grants_to_state_local_govts"
    params = {
        "filter": f"fiscal_year:eq:{fiscal_year}",
        "page[size]": "1000",
        "sort": "-fiscal_year",
    }
    cache_key = f"treasury_grants_{fiscal_year}"
    data = cached_request(url, cache_key, params=params)

    if data and "data" in data:
        return data["data"]

    # Fallback: try a broader endpoint
    url_alt = f"{TREASURY_API_BASE}/v1/accounting/mts/mts_table_5"
    params_alt = {
        "filter": f"record_fiscal_year:eq:{fiscal_year}",
        "page[size]": "1000",
    }
    cache_key_alt = f"treasury_mts5_{fiscal_year}"
    data_alt = cached_request(url_alt, cache_key_alt, params=params_alt)

    if data_alt and "data" in data_alt:
        return data_alt["data"]

    logger.warning("No Treasury grant data found for fiscal year %d", fiscal_year)
    return []


def _fetch_federal_spending_by_state(fiscal_year: int) -> dict[str, float]:
    """
    Fetch total federal spending by state.

    Uses the USAspending-style endpoint from Treasury Fiscal Data.
    Returns dict mapping state abbreviation to total federal dollars received.
    """
    url = f"{TREASURY_API_BASE}/v1/accounting/od/state_federal_spending"
    params = {
        "filter": f"fiscal_year:eq:{fiscal_year}",
        "page[size]": "200",
        "sort": "state_name",
    }
    cache_key = f"treasury_state_spending_{fiscal_year}"
    data = cached_request(url, cache_key, params=params)

    result = {}
    if data and "data" in data:
        for rec in data["data"]:
            state_name = rec.get("state_name", "").strip()
            # Match state name to abbreviation
            abbr = _name_to_abbr(state_name)
            if abbr is None:
                continue
            try:
                amount = float(rec.get("total_federal_spending", 0) or 0)
            except (ValueError, TypeError):
                amount = 0.0
            result[abbr] = result.get(abbr, 0.0) + amount

    return result


def _name_to_abbr(name: str) -> str | None:
    """Convert a state name to its abbreviation."""
    name_lower = name.lower().strip()
    for abbr, full_name in STATE_NAMES.items():
        if full_name.lower() == name_lower:
            return abbr
    return None


def _calculate_dependency_ratios(
    federal_spending: dict[str, float],
    census_tax_path: str | None = None,
) -> dict[str, float]:
    """
    Calculate federal dependency ratio for each state.

    Dependency ratio = federal_dollars_received / state_own_source_revenue.
    Higher values indicate greater reliance on federal transfers.
    """
    ratios = {}

    # Try to load state tax revenue data for the denominator
    if census_tax_path is None:
        census_tax_path = os.path.join(PROCESSED_DIR, "census_tax_collections.json")

    tax_data = load_json(census_tax_path)
    if tax_data is None:
        logger.warning(
            "Census tax data not available at %s; dependency ratios will use "
            "federal spending values only.",
            census_tax_path,
        )
        return ratios

    for abbr, fed_amount in federal_spending.items():
        state_tax = tax_data.get(abbr, {})
        own_revenue = state_tax.get("total_tax_revenue", 0.0)
        if own_revenue and own_revenue > 0:
            ratios[abbr] = round(fed_amount / own_revenue, 4)
        else:
            ratios[abbr] = None

    return ratios


def fetch_treasury_fiscal(year: int | None = None) -> dict:
    """
    Main entry point: fetch Treasury fiscal data and build state profiles.

    Returns a dict keyed by state abbreviation.
    """
    ensure_dirs()
    target_year = year or DEFAULT_YEAR
    logger.info("Fetching Treasury fiscal data for year %d", target_year)

    # Fetch federal spending by state
    federal_spending = _fetch_federal_spending_by_state(target_year)

    # Calculate dependency ratios if census data is available
    dependency_ratios = _calculate_dependency_ratios(federal_spending)

    # Build state-level output
    state_data = {}
    for abbr in sorted(STATE_FIPS.keys()):
        rec = {
            "state": abbr,
            "name": STATE_NAMES.get(abbr, ""),
            "year": target_year,
            "federal_spending_received": federal_spending.get(abbr),
            "federal_dependency_ratio": dependency_ratios.get(abbr),
        }
        state_data[abbr] = rec

    # Quality checks
    states_with_data = {k: v for k, v in state_data.items() if v.get("federal_spending_received") is not None}
    check_state_coverage(states_with_data, "Treasury Federal Transfers")
    check_nulls(
        list(state_data.values()),
        ["federal_spending_received"],
        "Treasury Federal Transfers",
    )

    # Save
    output_path = os.path.join(PROCESSED_DIR, "treasury_federal_transfers.json")
    save_json(state_data, output_path)
    logger.info("Saved Treasury federal transfers to %s", output_path)

    return state_data


if __name__ == "__main__":
    fetch_treasury_fiscal()
