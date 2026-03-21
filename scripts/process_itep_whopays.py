"""
Process ITEP Who Pays? reference data into pipeline-ready format.

Reads manually-maintained ITEP distributional data from data/reference/,
validates it, and outputs Chart.js-ready effective rate datasets.

Output: data/processed/itep_distributional.json
"""

import os

from scripts.config import PROCESSED_DIR, REFERENCE_DIR
from scripts.utils import load_json, save_json, setup_logging

logger = setup_logging("pipeline.itep")

REFERENCE_FILE = os.path.join(REFERENCE_DIR, "itep_whopays.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "itep_distributional.json")


def _validate_rates(abbr: str, rates: list) -> list[str]:
    """Validate a state's rate array. Returns list of error strings."""
    errors = []
    if not isinstance(rates, list):
        errors.append(f"{abbr}: rates is not a list")
        return errors
    if len(rates) != 7:
        errors.append(f"{abbr}: rates has {len(rates)} elements, expected 7")
        return errors
    for i, val in enumerate(rates):
        if val is None:
            continue
        if not isinstance(val, (int, float)):
            errors.append(f"{abbr}: rates[{i}] is not a number: {val}")
        elif val < 0 or val > 30:
            errors.append(f"{abbr}: rates[{i}] = {val} is outside 0-30% range")
    return errors


def process_itep_whopays() -> dict:
    """
    Read ITEP reference data, validate, and output Chart.js-ready datasets.

    Returns the processed data dict keyed by state abbreviation.
    """
    raw = load_json(REFERENCE_FILE)
    if raw is None:
        logger.warning("ITEP reference file not found at %s", REFERENCE_FILE)
        return {}

    metadata = raw.get("_metadata", {})
    states_data = raw.get("states", {})
    national_avg = metadata.get("national_average", [11.4, 10.9, 10.2, 9.8, 9.4, 8.3, 7.2])
    quintile_labels = metadata.get("quintile_labels", [
        "Lowest 20%", "Second 20%", "Middle 20%", "Fourth 20%",
        "Next 15%", "Next 4%", "Top 1%",
    ])

    output = {}
    populated = 0
    partial = 0

    for abbr, state_entry in states_data.items():
        rates = state_entry.get("rates")
        if rates is None:
            continue

        errors = _validate_rates(abbr, rates)
        if errors:
            for err in errors:
                logger.error("Validation: %s", err)
            continue

        # Check if full or partial data
        non_null = sum(1 for r in rates if r is not None)
        if non_null == 7:
            populated += 1
        elif non_null > 0:
            partial += 1
            logger.info("%s: partial ITEP data (%d/7 quintiles)", abbr, non_null)

        # Build Chart.js-ready dataset
        output[abbr] = {
            "labels": quintile_labels,
            "datasets": [
                {
                    "label": "ITEP Effective Rate (%)",
                    "data": rates,
                    "backgroundColor": "#2d6a4f",
                },
                {
                    "label": "National Average (%)",
                    "data": national_avg,
                    "backgroundColor": "#7fb3d8",
                },
            ],
        }

    save_json(output, OUTPUT_FILE)
    logger.info(
        "ITEP processing complete: %d full, %d partial, %d total states",
        populated, partial, len(output),
    )
    return output


if __name__ == "__main__":
    process_itep_whopays()
