"""
Process Tax Foundation State Tax Competitiveness Index reference data.

Reads manually-maintained ranking data from data/reference/,
validates it, and outputs pipeline-ready competitiveness index data.

Output: data/processed/tax_foundation_index.json
"""

import os

from scripts.config import PROCESSED_DIR, REFERENCE_DIR
from scripts.utils import load_json, save_json, setup_logging

logger = setup_logging("pipeline.tax_foundation")

REFERENCE_FILE = os.path.join(REFERENCE_DIR, "tax_foundation_index.json")
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "tax_foundation_index.json")

RANK_FIELDS = [
    "overall_rank",
    "corporate_rank",
    "individual_income_rank",
    "sales_tax_rank",
    "property_tax_rank",
    "unemployment_insurance_rank",
]


def _validate_state(abbr: str, data: dict) -> list[str]:
    """Validate a state's rank data. Returns list of error strings."""
    errors = []
    for field in RANK_FIELDS:
        val = data.get(field)
        if val is None:
            continue
        if not isinstance(val, int):
            errors.append(f"{abbr}: {field} is not an integer: {val}")
        elif val < 1 or val > 51:
            errors.append(f"{abbr}: {field} = {val} is outside 1-51 range")
    return errors


def process_tax_foundation() -> dict:
    """
    Read Tax Foundation reference data, validate, and output processed data.

    Returns the processed data dict keyed by state abbreviation.
    """
    raw = load_json(REFERENCE_FILE)
    if raw is None:
        logger.warning("Tax Foundation reference file not found at %s", REFERENCE_FILE)
        return {}

    states_data = raw.get("states", {})
    output = {}
    full = 0
    partial = 0

    for abbr, state_entry in states_data.items():
        errors = _validate_state(abbr, state_entry)
        if errors:
            for err in errors:
                logger.error("Validation: %s", err)
            continue

        # Build competitiveness index dict
        index = {}
        non_null = 0
        for field in RANK_FIELDS:
            val = state_entry.get(field)
            index[field] = val
            if val is not None:
                non_null += 1

        if non_null == len(RANK_FIELDS):
            full += 1
        elif non_null > 0:
            partial += 1
            logger.info("%s: partial TF data (%d/%d ranks)", abbr, non_null, len(RANK_FIELDS))

        output[abbr] = index

    save_json(output, OUTPUT_FILE)
    logger.info(
        "Tax Foundation processing complete: %d full, %d partial, %d total states",
        full, partial, len(output),
    )
    return output


if __name__ == "__main__":
    process_tax_foundation()
