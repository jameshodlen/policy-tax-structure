"""
Process Lincoln Institute property tax reference data.

Reads city-level property tax rates and state policy attributes from
data/reference/lincoln_property_tax.json, validates the data, computes
state-level summaries, and outputs pipeline-ready data.

Output: data/processed/lincoln_property_tax.json
"""

import os
from statistics import mean

from scripts.config import PROCESSED_DIR, REFERENCE_DIR
from scripts.utils import load_json, save_json, setup_logging

logger = setup_logging("pipeline.lincoln_property")

REFERENCE_FILE = os.path.join(REFERENCE_DIR, "lincoln_property_tax.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "lincoln_property_tax.json")

RATE_FIELDS = ["homestead_rate", "commercial_rate", "industrial_rate", "apartment_rate"]

REQUIRED_CITY_FIELDS = ["city"] + RATE_FIELDS

REQUIRED_STATE_FIELDS = [
    "assessment_practice",
    "classification",
    "circuit_breaker",
]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_rate(abbr: str, city_name: str, field: str, value) -> list[str]:
    """Validate that a tax rate is a positive number between 0 and 10."""
    errors = []
    if not isinstance(value, (int, float)):
        errors.append(f"{abbr}/{city_name}: {field} is not a number: {value}")
    elif value <= 0 or value > 10:
        errors.append(f"{abbr}/{city_name}: {field} = {value} is outside (0, 10] range")
    return errors


def _validate_city(abbr: str, city: dict) -> list[str]:
    """Validate a single city entry. Returns list of error strings."""
    errors = []
    city_name = city.get("city", "<unknown>")

    for field in REQUIRED_CITY_FIELDS:
        if field not in city or city[field] is None:
            errors.append(f"{abbr}/{city_name}: missing required field '{field}'")
            continue
        if field in RATE_FIELDS:
            errors.extend(_validate_rate(abbr, city_name, field, city[field]))

    return errors


def _validate_state(abbr: str, state_data: dict) -> list[str]:
    """Validate a state entry. Returns list of error strings."""
    errors = []

    for field in REQUIRED_STATE_FIELDS:
        if field not in state_data:
            errors.append(f"{abbr}: missing required field '{field}'")

    cities = state_data.get("cities")
    if not isinstance(cities, list) or len(cities) == 0:
        errors.append(f"{abbr}: no city data found")
        return errors

    for city in cities:
        errors.extend(_validate_city(abbr, city))

    return errors


# ---------------------------------------------------------------------------
# State-level summaries
# ---------------------------------------------------------------------------

def _build_state_summary(cities: list[dict]) -> dict:
    """Compute aggregate statistics across a state's cities."""
    homestead_rates = [c["homestead_rate"] for c in cities]
    commercial_rates = [c["commercial_rate"] for c in cities]

    avg_homestead = round(mean(homestead_rates), 2)
    avg_commercial = round(mean(commercial_rates), 2)

    min_rate = min(homestead_rates)
    max_rate = max(homestead_rates)
    rate_range = f"{min_rate:.2f}% - {max_rate:.2f}%"

    ratio = round(avg_commercial / avg_homestead, 2) if avg_homestead else None

    return {
        "avg_homestead_rate": avg_homestead,
        "rate_range": rate_range,
        "commercial_to_residential_ratio": ratio,
    }


def _build_relief_programs(state_data: dict) -> list[str]:
    """Extract a list of relief program names from state policy fields."""
    programs = []
    exemption = state_data.get("homestead_exemptions")
    if exemption:
        programs.append(exemption)
    cb_detail = state_data.get("circuit_breaker_detail")
    if cb_detail:
        programs.append(cb_detail)
    return programs


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_lincoln_property() -> dict:
    """
    Read Lincoln Institute property tax reference data, validate, compute
    state summaries, and output processed data.

    Returns the processed data dict keyed by state abbreviation.
    """
    raw = load_json(REFERENCE_FILE)
    if raw is None:
        logger.warning(
            "Lincoln property tax reference file not found at %s", REFERENCE_FILE
        )
        return {}

    states_data = raw.get("states", {})
    output = {}

    for abbr, state_entry in states_data.items():
        errors = _validate_state(abbr, state_entry)
        if errors:
            for err in errors:
                logger.error("Validation: %s", err)
            continue

        cities = state_entry["cities"]
        state_summary = _build_state_summary(cities)
        relief_programs = _build_relief_programs(state_entry)

        output[abbr] = {
            "cities": cities,
            "state_summary": state_summary,
            "assessment_practice": state_entry.get("assessment_practice"),
            "classification": state_entry.get("classification"),
            "circuit_breaker": state_entry.get("circuit_breaker"),
            "relief_programs": relief_programs,
        }

    save_json(output, OUTPUT_FILE)
    logger.info(
        "Lincoln property tax processing complete: %d states with city-level data",
        len(output),
    )
    return output


if __name__ == "__main__":
    process_lincoln_property()
