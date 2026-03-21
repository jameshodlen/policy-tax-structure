"""
Build per-state profile JSON files by merging all processed and reference data.

Reads processed JSON from each pipeline step plus reference data, merges into
unified profiles matching the hand-authored schema, and outputs Chart.js-ready
JSON for the docs site.

Output: docs/assets/data/{state_abbr}_profile.json
"""

import logging
import os
from datetime import date

from scripts.config import (
    PROCESSED_DIR,
    REFERENCE_DIR,
    SITE_DIR,
    STATE_FIPS,
    STATE_NAMES,
)
from scripts.utils import (
    ensure_dirs,
    load_json,
    save_json,
    setup_logging,
    validate_profile_schema,
)

logger = setup_logging("pipeline.build_profiles")

# Processed data file paths
PROCESSED_FILES = {
    "census_tax": os.path.join(PROCESSED_DIR, "census_tax_collections.json"),
    "bea_economic": os.path.join(PROCESSED_DIR, "bea_economic_context.json"),
    "fred_series": os.path.join(PROCESSED_DIR, "fred_economic_series.json"),
    "treasury": os.path.join(PROCESSED_DIR, "treasury_federal_transfers.json"),
    "itep_rates": os.path.join(PROCESSED_DIR, "itep_distributional.json"),
    "tax_foundation": os.path.join(PROCESSED_DIR, "tax_foundation_index.json"),
    "irs_migration": os.path.join(PROCESSED_DIR, "irs_soi_migration.json"),
    "lincoln_property": os.path.join(PROCESSED_DIR, "lincoln_property_tax.json"),
}

# Reference data file paths
REFERENCE_FILES = {
    "state_tax_structures": os.path.join(REFERENCE_DIR, "state_tax_structures.json"),
}

# Revenue composition category mapping: Census key -> display label
_REVENUE_CATEGORIES = [
    ("individual_income_total", "Individual Income Tax"),
    ("general_sales_total", "Sales & Use Tax"),
    ("corporate_income_total", "Corporate Income Tax"),
    ("selective_sales_total", "Excise Taxes"),
    ("property_total", "Property Tax (state)"),
]

_REVENUE_COLORS = [
    "#1e3a5f", "#2d6a4f", "#4a90d9", "#7fb3d8", "#b5d4e8", "#d4e6f1",
]

# States that get strict schema validation
_STRICT_STATES = {"MN", "WI"}


def _load_all_sources() -> dict[str, dict]:
    """Load all processed and reference data files."""
    sources = {}

    for name, path in PROCESSED_FILES.items():
        data = load_json(path)
        if data is None:
            logger.warning("Data source '%s' not found at %s — skipping", name, path)
        else:
            sources[name] = data
            logger.info("Loaded %s (%d entries)", name, len(data))

    for name, path in REFERENCE_FILES.items():
        data = load_json(path)
        if data is None:
            logger.warning("Reference data '%s' not found at %s — skipping", name, path)
        else:
            sources[name] = data
            logger.info("Loaded reference %s", name)

    return sources


def _build_revenue_composition(census_data: dict) -> dict | None:
    """
    Convert Census raw dollar amounts to percentage-based Chart.js pie chart.

    Returns a Chart.js-compatible dict with labels and datasets, or None if
    no census data is available.
    """
    if not census_data:
        return None

    # Calculate "Other" as license + severance
    other = (census_data.get("license_total") or 0.0) + (census_data.get("severance_total") or 0.0)

    # Collect raw amounts
    raw_values = []
    for key, _label in _REVENUE_CATEGORIES:
        raw_values.append(census_data.get(key) or 0.0)
    raw_values.append(other)

    total = sum(raw_values)
    if total <= 0:
        return None

    # Convert to percentages (rounded to nearest integer, matching hand-authored format)
    percentages = [round(v / total * 100) for v in raw_values]

    labels = [label for _key, label in _REVENUE_CATEGORIES] + ["Other"]

    return {
        "labels": labels,
        "datasets": [{
            "data": percentages,
            "backgroundColor": _REVENUE_COLORS[:len(labels)],
        }],
    }


def _build_economic_context(abbr: str, sources: dict[str, dict]) -> dict | None:
    """
    Merge BEA and FRED data into the economic_context block.

    BEA provides: per_capita_income, gdp (mapped to gdp_per_capita)
    FRED provides: unemployment_rate, median_household_income
    """
    bea = sources.get("bea_economic", {}).get(abbr, {})
    fred = sources.get("fred_series", {}).get(abbr, {})

    ctx = {
        "median_household_income": fred.get("median_household_income"),
        "per_capita_income": bea.get("per_capita_income"),
        "gdp_per_capita": bea.get("gdp"),
        "population": None,  # Not directly available from current pipeline sources
        "unemployment_rate": fred.get("unemployment_rate"),
    }

    # Return None only if all values are missing
    if all(v is None for v in ctx.values()):
        return None
    return ctx


def _build_federal_transfers(abbr: str, sources: dict[str, dict]) -> dict | None:
    """Extract Treasury federal transfer data for a state."""
    treasury = sources.get("treasury", {}).get(abbr, {})
    if not treasury:
        return None

    return {
        "federal_spending_received": treasury.get("federal_spending_received"),
        "federal_dependency_ratio": treasury.get("federal_dependency_ratio"),
    }


def _build_migration(abbr: str, sources: dict[str, dict]) -> dict | None:
    """Extract IRS SOI migration data for a state."""
    migration_data = sources.get("irs_migration", {})
    # Handle both top-level keyed and nested "states" structures
    states = migration_data.get("states", migration_data)
    state_mig = states.get(abbr, {})
    if not state_mig or state_mig.get("net_returns") is None:
        return None

    net_agi = state_mig.get("net_agi")
    net_agi_fmt = None
    if net_agi is not None:
        sign = "-" if net_agi < 0 else ""
        abs_agi = abs(net_agi)
        if abs_agi >= 1_000_000_000:
            net_agi_fmt = f"{sign}${abs_agi / 1_000_000_000:.1f}B"
        elif abs_agi >= 1_000_000:
            net_agi_fmt = f"{sign}${abs_agi / 1_000_000:.0f}M"
        else:
            net_agi_fmt = f"{sign}${abs_agi:,.0f}"

    return {
        "tax_year": migration_data.get("_metadata", {}).get("tax_year"),
        "net_returns": state_mig.get("net_returns"),
        "net_agi": net_agi,
        "net_agi_formatted": net_agi_fmt,
        "top_inflows": state_mig.get("top_inflows", []),
        "top_outflows": state_mig.get("top_outflows", []),
    }


def build_state_profile(abbr: str, sources: dict[str, dict]) -> dict:
    """
    Build a single state's profile by merging all data sources.

    Output matches the hand-authored schema used by mn_profile.json and
    wi_profile.json, with Chart.js-ready datasets at top-level keys.
    """
    ref = sources.get("state_tax_structures", {})
    template = ref.get("_template", {})
    state_ref = ref.get(abbr, template)

    profile = {
        "state": STATE_NAMES.get(abbr, ""),
        "abbreviation": abbr,
        "last_updated": date.today().isoformat(),
    }

    # tax_structure: from reference data
    profile["tax_structure"] = state_ref.get("tax_structure", template.get("tax_structure"))

    # revenue_composition: Census data converted to percentages
    census = sources.get("census_tax", {}).get(abbr, {})
    profile["revenue_composition"] = _build_revenue_composition(census)

    # effective_rates_by_quintile: from ITEP processed data (already Chart.js-ready)
    profile["effective_rates_by_quintile"] = sources.get("itep_rates", {}).get(abbr)

    # economic_context: merged BEA + FRED
    profile["economic_context"] = _build_economic_context(abbr, sources)

    # competitiveness_index: from Tax Foundation processed data
    profile["competitiveness_index"] = sources.get("tax_foundation", {}).get(abbr)

    # key_facts: from reference data
    profile["key_facts"] = state_ref.get("key_facts", template.get("key_facts"))

    # federal_transfers: from Treasury
    ft = _build_federal_transfers(abbr, sources)
    if ft is not None:
        profile["federal_transfers"] = ft

    # migration: from IRS SOI migration data
    mig = _build_migration(abbr, sources)
    if mig is not None:
        profile["migration"] = mig

    # property_tax: from Lincoln Institute processed data
    lincoln = sources.get("lincoln_property", {}).get(abbr)
    if lincoln is not None:
        profile["property_tax"] = lincoln

    return profile


def build_all_profiles(state_filter: str | None = None) -> dict[str, dict]:
    """
    Build profiles for all states (or a single state if *state_filter* is set).

    Returns a dict of abbr -> profile.
    """
    ensure_dirs()
    sources = _load_all_sources()

    if not sources:
        logger.error("No data sources found. Run fetch/process scripts first.")
        return {}

    states = [state_filter.upper()] if state_filter else sorted(STATE_FIPS.keys())
    profiles = {}

    for abbr in states:
        if abbr not in STATE_FIPS:
            logger.warning("Unknown state abbreviation: %s — skipping", abbr)
            continue

        profile = build_state_profile(abbr, sources)

        # Validate schema — only strict when all data sources are present
        has_all_sources = all(
            k in sources for k in ("census_tax", "bea_economic", "fred_series",
                                   "itep_rates", "tax_foundation", "state_tax_structures")
        )
        strict = abbr in _STRICT_STATES and has_all_sources
        errors = validate_profile_schema(profile, strict=strict)
        if errors:
            level = logging.ERROR if strict else logging.WARNING
            for err in errors:
                logger.log(level, "%s: %s", abbr, err)
            if strict:
                raise ValueError(
                    f"Strict schema validation failed for {abbr}: {errors}"
                )

        profiles[abbr] = profile

        # Write individual profile JSON
        out_path = os.path.join(SITE_DIR, f"{abbr.lower()}_profile.json")
        save_json(profile, out_path)

    logger.info("Built %d state profile(s) in %s", len(profiles), SITE_DIR)

    # Write combined index
    index = {
        abbr: {
            "name": p["state"],
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
