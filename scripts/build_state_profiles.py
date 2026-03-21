"""
Build per-state profile JSON files by merging all processed data sources.

Reads processed JSON from each fetch script, merges into unified profiles,
and outputs Chart.js-ready JSON for the docs site.

Output: docs/assets/data/{state_abbr}_profile.json
"""

import logging
import os
import sys

from scripts.config import (
    PROCESSED_DIR,
    SITE_DIR,
    STATE_FIPS,
    STATE_NAMES,
)
from scripts.utils import (
    ensure_dirs,
    load_json,
    save_json,
    setup_logging,
)

logger = setup_logging("pipeline.build_profiles")

# Processed data file paths
DATA_FILES = {
    "census_tax": os.path.join(PROCESSED_DIR, "census_tax_collections.json"),
    "bea_economic": os.path.join(PROCESSED_DIR, "bea_economic_context.json"),
    "fred_series": os.path.join(PROCESSED_DIR, "fred_economic_series.json"),
    "treasury": os.path.join(PROCESSED_DIR, "treasury_federal_transfers.json"),
}


def _load_all_sources() -> dict[str, dict]:
    """Load all processed data files. Returns a dict of source_name -> data."""
    sources = {}
    for name, path in DATA_FILES.items():
        data = load_json(path)
        if data is None:
            logger.warning("Data source '%s' not found at %s — skipping", name, path)
        else:
            sources[name] = data
            logger.info("Loaded %s (%d states)", name, len(data))
    return sources


def _build_tax_pie_chart(tax_data: dict) -> dict:
    """
    Build a Chart.js-compatible pie chart dataset for tax revenue composition.

    Returns a dict with 'labels' and 'datasets' ready for Chart.js.
    """
    categories = [
        ("Individual Income", "individual_income_total"),
        ("Corporate Income", "corporate_income_total"),
        ("General Sales", "general_sales_total"),
        ("Selective Sales", "selective_sales_total"),
        ("Property", "property_total"),
        ("License", "license_total"),
        ("Severance", "severance_total"),
    ]

    labels = []
    values = []
    colors = [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
        "#59a14f", "#edc948", "#b07aa1",
    ]

    for label, key in categories:
        val = tax_data.get(key, 0.0)
        if val and val > 0:
            labels.append(label)
            values.append(round(val, 2))

    return {
        "type": "pie",
        "labels": labels,
        "datasets": [{
            "label": "Tax Revenue by Category",
            "data": values,
            "backgroundColor": colors[:len(values)],
        }],
    }


def _build_economic_bar_chart(profile: dict) -> dict:
    """
    Build a Chart.js-compatible bar chart for key economic indicators.
    """
    indicators = []
    values = []

    if profile.get("per_capita_income") is not None:
        indicators.append("Per Capita Income ($)")
        values.append(round(profile["per_capita_income"], 2))

    if profile.get("median_household_income") is not None:
        indicators.append("Median Household Income ($)")
        values.append(round(profile["median_household_income"], 2))

    if profile.get("unemployment_rate") is not None:
        indicators.append("Unemployment Rate (%)")
        values.append(round(profile["unemployment_rate"], 2))

    if profile.get("regional_price_parity") is not None:
        indicators.append("Regional Price Parity")
        values.append(round(profile["regional_price_parity"], 2))

    return {
        "type": "bar",
        "labels": indicators,
        "datasets": [{
            "label": "Economic Indicators",
            "data": values,
            "backgroundColor": "#4e79a7",
        }],
    }


def _build_revenue_comparison_chart(profile: dict) -> dict:
    """
    Build a Chart.js bar chart comparing own-source revenue vs federal transfers.
    """
    labels = []
    values = []

    if profile.get("total_tax_revenue") is not None:
        labels.append("State Tax Revenue")
        values.append(round(profile["total_tax_revenue"], 2))

    if profile.get("federal_spending_received") is not None:
        labels.append("Federal Transfers")
        values.append(round(profile["federal_spending_received"], 2))

    return {
        "type": "bar",
        "labels": labels,
        "datasets": [{
            "label": "Revenue Sources (thousands $)",
            "data": values,
            "backgroundColor": ["#59a14f", "#e15759"],
        }],
    }


def build_state_profile(abbr: str, sources: dict[str, dict]) -> dict:
    """
    Build a single state's profile by merging all data sources.

    Returns the complete profile dict.
    """
    profile = {
        "state": abbr,
        "name": STATE_NAMES.get(abbr, ""),
    }

    # Census tax data
    census = sources.get("census_tax", {}).get(abbr, {})
    for key, val in census.items():
        if key not in ("state", "name"):
            profile[key] = val

    # BEA economic data
    bea = sources.get("bea_economic", {}).get(abbr, {})
    for key in ("personal_income", "per_capita_income", "gdp", "regional_price_parity"):
        if key in bea:
            profile[key] = bea[key]
    if "year" in bea and "year" not in profile:
        profile["year"] = bea["year"]

    # FRED series
    fred = sources.get("fred_series", {}).get(abbr, {})
    for key in (
        "unemployment_rate", "unemployment_rate_date",
        "median_household_income", "median_household_income_date",
    ):
        if key in fred:
            profile[key] = fred[key]

    # Treasury fiscal data
    treasury = sources.get("treasury", {}).get(abbr, {})
    for key in ("federal_spending_received", "federal_dependency_ratio"):
        if key in treasury:
            profile[key] = treasury[key]

    # Build Chart.js datasets
    charts = {}
    if census:
        charts["tax_composition"] = _build_tax_pie_chart(census)
    charts["economic_indicators"] = _build_economic_bar_chart(profile)
    charts["revenue_comparison"] = _build_revenue_comparison_chart(profile)
    profile["charts"] = charts

    return profile


def build_all_profiles(state_filter: str | None = None) -> dict[str, dict]:
    """
    Build profiles for all states (or a single state if *state_filter* is set).

    Returns a dict of abbr -> profile.
    """
    ensure_dirs()
    sources = _load_all_sources()

    if not sources:
        logger.error("No processed data sources found. Run fetch scripts first.")
        return {}

    states = [state_filter.upper()] if state_filter else sorted(STATE_FIPS.keys())
    profiles = {}

    for abbr in states:
        if abbr not in STATE_FIPS:
            logger.warning("Unknown state abbreviation: %s — skipping", abbr)
            continue

        profile = build_state_profile(abbr, sources)
        profiles[abbr] = profile

        # Write individual profile JSON
        out_path = os.path.join(SITE_DIR, f"{abbr.lower()}_profile.json")
        save_json(profile, out_path)

    logger.info("Built %d state profile(s) in %s", len(profiles), SITE_DIR)

    # Also write a combined index
    index = {
        abbr: {
            "name": p["name"],
            "file": f"{abbr.lower()}_profile.json",
        }
        for abbr, p in profiles.items()
    }
    save_json(index, os.path.join(SITE_DIR, "state_index.json"))
    logger.info("Wrote state_index.json")

    return profiles


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build state profile JSON files")
    parser.add_argument(
        "--state", type=str, default=None,
        help="Build profile for a single state (e.g., CA)",
    )
    args = parser.parse_args()
    build_all_profiles(state_filter=args.state)
