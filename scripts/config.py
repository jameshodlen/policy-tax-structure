"""
Central configuration for the tax structure research data pipeline.

Provides API endpoints, state FIPS codes, directory paths, and API key loading.
"""

import os
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on environment variables directly

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root (two levels up from this file: scripts/ -> project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
SITE_DIR = os.path.join(PROJECT_ROOT, "docs", "assets", "data")
CACHE_DIR = os.path.join(RAW_DIR, "cache")

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
CENSUS_API_BASE = "https://api.census.gov/data"
BEA_API_BASE = "https://apps.bea.gov/api"
FRED_API_BASE = "https://api.stlouisfed.org/fred"
TREASURY_API_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# ---------------------------------------------------------------------------
# API keys (loaded from environment / .env)
# ---------------------------------------------------------------------------
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")
BEA_API_KEY = os.environ.get("BEA_API_KEY", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
# Treasury Fiscal Data API does not require a key.

# ---------------------------------------------------------------------------
# State FIPS codes — all 50 states + DC
# ---------------------------------------------------------------------------
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "DC": "11", "FL": "12",
    "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
    "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23",
    "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33",
    "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
    "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
    "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
    "WY": "56",
}

# Reverse lookup: FIPS -> abbreviation
FIPS_TO_STATE = {v: k for k, v in STATE_FIPS.items()}

# Full state names for display purposes
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

# ---------------------------------------------------------------------------
# Data-year defaults
# ---------------------------------------------------------------------------
DEFAULT_YEAR = 2022
YEAR_RANGE = list(range(2015, 2024))


def check_api_key(name: str, value: str) -> bool:
    """Return True if the key is set; log a warning otherwise."""
    if not value:
        logger.warning(
            "API key %s is not set. Set it in a .env file or as an "
            "environment variable. Requests that require this key will be skipped.",
            name,
        )
        return False
    return True
