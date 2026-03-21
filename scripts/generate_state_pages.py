"""
Generate MkDocs markdown pages for state tax profiles.

Reads profile JSON from docs/assets/data/{abbr}_profile.json and reference
data from data/reference/, then renders markdown pages using the WI/MN
template structure.

Output: docs/states/{state_slug}.md for each state
"""

import argparse
import os

from jinja2 import Environment

from scripts.config import (
    PROJECT_ROOT,
    REFERENCE_DIR,
    SITE_DIR,
    STATE_FIPS,
    STATE_NAMES,
)
from scripts.utils import load_json, setup_logging, ensure_dirs

logger = setup_logging("pipeline.generate_pages")

STATES_DIR = os.path.join(PROJECT_ROOT, "docs", "states")

# States with no individual income tax
NO_INCOME_TAX = {"AK", "FL", "NV", "NH", "SD", "TN", "TX", "WA", "WY"}

# States with flat income tax (as of 2026)
FLAT_TAX = {"AZ", "CO", "GA", "ID", "IL", "IN", "IA", "KY", "MI", "MS", "MT", "NC", "ND", "PA", "UT"}

# ITEP's 10 most regressive states
ITEP_MOST_REGRESSIVE = {"FL", "WA", "TN", "PA", "NV", "SD", "TX", "IL", "AR", "LA"}

# ITEP's 6 states that reduce inequality (+ DC)
ITEP_PROGRESSIVE = {"CA", "ME", "MN", "NJ", "NY", "VT", "DC"}

# State peer pairs for comparison sections
STATE_PEERS = {
    "WI": "MN", "MN": "WI",
    "OR": "WA", "WA": "OR",
    "CA": "NV", "NV": "CA",
    "TN": "NC", "NC": "TN",
    "TX": "OK", "OK": "TX",
    "FL": "GA", "GA": "FL",
    "IL": "IN", "IN": "IL",
    "NY": "NJ", "NJ": "NY",
    "PA": "DE", "DE": "PA",
    "OH": "MI", "MI": "OH",
    "CO": "UT", "UT": "CO",
    "AK": "WY", "WY": "AK",
    "SD": "ND", "ND": "SD",
    "NE": "KS", "KS": "NE",
    "IA": "MO", "MO": "IA",
    "AR": "MS", "MS": "AR",
    "LA": "AL", "AL": "LA",
    "SC": "VA", "VA": "SC",
    "CT": "MA", "MA": "CT",
    "VT": "NH", "NH": "VT",
    "ME": "RI", "RI": "ME",
    "MD": "DC", "DC": "MD",
    "HI": "AZ", "AZ": "HI",
    "NM": "AZ",
    "WV": "KY", "KY": "WV",
    "ID": "MT", "MT": "ID",
}


def _state_slug(name: str) -> str:
    """Convert state name to URL slug (e.g., 'New York' -> 'new-york')."""
    return name.lower().replace(" ", "-")


def _ordinal(n: int) -> str:
    """Convert integer to ordinal string (1 -> '1st', 2 -> '2nd', etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _format_currency(amount: int | float | None) -> str:
    """Format a number as currency."""
    if amount is None:
        return "N/A"
    return f"${amount:,.0f}"


def _build_overview(abbr: str, profile: dict, tf_data: dict | None) -> str:
    """Generate the overview paragraph based on available data."""
    name = profile.get("state", "")
    ts = profile.get("tax_structure") or {}
    ci = profile.get("competitiveness_index") or {}
    income_type = ts.get("income_tax_type")
    brackets = ts.get("income_tax_brackets", [])
    sales_rate = ts.get("sales_tax_rate")
    corp_rate = ts.get("corporate_tax_rate")
    overall_rank = ci.get("overall_rank")

    parts = []

    # Income tax description
    if abbr in NO_INCOME_TAX:
        parts.append(f"{name} does not levy an individual income tax")
    elif income_type == "graduated" and brackets:
        top_rate = brackets[-1].get("rate", 0)
        parts.append(
            f"{name} employs a graduated individual income tax with "
            f"{len(brackets)} brackets and a top rate of {top_rate}%"
        )
    elif income_type == "flat" and brackets:
        rate = brackets[0].get("rate", 0)
        parts.append(f"{name} employs a flat individual income tax at {rate}%")
    elif income_type:
        parts.append(f"{name} has a {income_type} individual income tax")
    else:
        parts.append(f"{name}'s tax structure")

    # Sales tax
    if sales_rate is not None:
        parts[0] += f", a {sales_rate}% state sales tax"
    elif abbr in NO_INCOME_TAX:
        parts[0] += ", relying instead on sales taxes, property taxes, and other revenue sources"

    # Corporate tax
    if corp_rate is not None:
        parts[0] += f", and a {corp_rate}% corporate tax rate"

    parts[0] += "."

    # ITEP assessment
    if abbr in ITEP_PROGRESSIVE:
        if abbr == "DC":
            parts.append(
                "The District of Columbia is one of only seven jurisdictions that ITEP "
                "identifies as reducing income inequality through its tax code."
            )
        else:
            parts.append(
                f"{name} is one of only six states (plus DC) that ITEP identifies "
                "as reducing income inequality through its tax code."
            )
    elif abbr in ITEP_MOST_REGRESSIVE:
        parts.append(
            f"ITEP ranks {name}'s tax system among the 10 most regressive in "
            "the nation, with lower-income households paying a higher effective "
            "tax rate than wealthier residents."
        )

    # Tax Foundation rank
    if overall_rank is not None:
        parts.append(
            f"The Tax Foundation ranks {name} {_ordinal(overall_rank)} on its "
            "State Tax Competitiveness Index."
        )

    return " ".join(parts)


def _build_glance_cards(abbr: str, profile: dict) -> str:
    """Build the Tax Structure at a Glance card section."""
    ts = profile.get("tax_structure") or {}
    ci = profile.get("competitiveness_index") or {}
    brackets = ts.get("income_tax_brackets", [])
    sales_rate = ts.get("sales_tax_rate")
    corp_rate = ts.get("corporate_tax_rate")
    overall_rank = ci.get("overall_rank")
    local_sales = ts.get("local_sales_tax")

    # Income tax card
    if abbr in NO_INCOME_TAX:
        income_val, income_detail = "None", "No individual income tax"
    elif brackets:
        rates = [b.get("rate", 0) for b in brackets]
        if len(set(rates)) == 1:
            income_val = f"{rates[0]}%"
            income_detail = "Flat rate"
        else:
            income_val = f"{min(rates)}%\u2013{max(rates)}%"
            income_detail = f"{len(brackets)} brackets, graduated"
    else:
        income_val, income_detail = "\u2014", "Data pending"

    # Sales tax card
    if sales_rate is not None:
        sales_val = f"{sales_rate}%"
        if local_sales is True:
            sales_detail = "Plus local sales taxes"
        elif local_sales is False:
            sales_detail = "No local sales taxes"
        else:
            sales_detail = "State rate"
    else:
        sales_val, sales_detail = "\u2014", "Data pending"

    # Corporate tax card
    if corp_rate is not None:
        corp_val, corp_detail = f"{corp_rate}%", "Single rate"
    else:
        corp_val, corp_detail = "\u2014", "Data pending"

    # Competitiveness card
    if overall_rank is not None:
        comp_val, comp_detail = f"#{overall_rank}", "Tax Foundation Index"
    else:
        comp_val, comp_detail = "\u2014", "Data pending"

    return f"""<div class="tax-glance" markdown>
<div class="card" markdown>
<div class="label">Income Tax</div>
<div class="value">{income_val}</div>
<div class="detail">{income_detail}</div>
</div>
<div class="card" markdown>
<div class="label">Sales Tax</div>
<div class="value">{sales_val}</div>
<div class="detail">{sales_detail}</div>
</div>
<div class="card" markdown>
<div class="label">Corporate Tax</div>
<div class="value">{corp_val}</div>
<div class="detail">{corp_detail}</div>
</div>
<div class="card" markdown>
<div class="label">Competitiveness</div>
<div class="value">{comp_val}</div>
<div class="detail">{comp_detail}</div>
</div>
</div>"""


TEMPLATE = """\
# {{ state_name }} Tax Structure

> **Last updated**: March 2026 | **Data sources**: Census Bureau, BEA, IRS SOI, ITEP, Tax Foundation

## Overview

{{ overview }}

## Tax Structure at a Glance

{{ glance_cards }}

{% if has_brackets and not no_income_tax -%}
### Income Tax Brackets (Single Filer, 2025)

| Taxable Income | Rate |
|---------------|------|
{% for b in brackets -%}
| {{ b.range }} | {{ b.rate }}% |
{% endfor %}
{% elif no_income_tax -%}
### Income Tax

{{ state_name }} does not levy an individual income tax. This places it among nine states that forgo this revenue source, relying instead on sales taxes, property taxes, and other revenue streams.

{% endif -%}

### Other Key Features

| Category | Detail |
|----------|--------|
| **Property Tax** | {{ property_tax_admin or 'Data pending' }} |
| **Estate Tax** | {{ estate_tax_text }} |
| **Notable Credits** | {{ notable_credits or 'Data pending' }} |
| **PTET Status** | {{ ptet_text }} |
| **Federal Conformity** | {{ conformity_text }} |

## Revenue Composition

How {{ state_name }} generates its state tax revenue, by source:

{% if has_revenue_data -%}
<div class="chart-container" markdown>
<canvas data-chart-type="pie"
        data-source="../assets/data/{{ abbr_lower }}_profile.json"
        data-key="revenue_composition">
</canvas>
</div>
{% else -%}
!!! info "Revenue Data Pending"
    Revenue composition data for {{ state_name }} will be available after the next Census data pipeline run.
{% endif %}

## Who Pays? Effective Tax Rates by Income

{% if has_itep_data -%}
<div class="chart-container" markdown>
<canvas data-chart-type="bar"
        data-source="../assets/data/{{ abbr_lower }}_profile.json"
        data-key="effective_rates_by_quintile">
</canvas>
</div>

{% if itep_partial -%}
!!! note "Partial distributional data"
    Full quintile data is not yet available for {{ state_name }}. The chart shows the effective tax rates for the lowest-income 20% and highest-income 1% only. See [Who Actually Pays?](../analysis/who-actually-pays.md) for methodology and full data availability.

{% endif -%}
=== "Tax Foundation View"

{% if has_tf_data -%}
    {{ state_name }} ranks **{{ tf_rank_text }}** on the State Tax Competitiveness Index (2024).
{% else -%}
    Tax Foundation competitiveness data not yet available for {{ state_name }}.
{% endif %}

=== "ITEP View"

{% if is_progressive -%}
    {{ state_name }} is one of only **six states plus DC** whose tax system **reduces income inequality** according to ITEP's analysis.
{% elif is_regressive -%}
    ITEP ranks {{ state_name }}'s tax system among the **10 most regressive** in the nation.
{% else -%}
    ITEP distributional analysis for {{ state_name }} shows the effective state and local tax rates by income group.
{% endif %}

=== "Primary Source Data"

    State tax data from Census Bureau and economic indicators from BEA/FRED.
{% else -%}
!!! info "Distributional Data Pending"
    ITEP distributional data is not yet available for {{ state_name }}. Data collection is in progress. See [Who Actually Pays?](../analysis/who-actually-pays.md) for methodology.
{% endif %}

## Economic Context

{% if has_economic_data -%}
| Metric | {{ state_name }} | National Median |
|--------|-----------|----------------|
| Median Household Income | {{ econ.median_household_income_fmt }} | $74,580 |
| Per Capita Income | {{ econ.per_capita_income_fmt }} | $37,638 |
| GDP Per Capita | {{ econ.gdp_per_capita_fmt }} | $63,444 |
| Unemployment Rate | {{ econ.unemployment_rate_fmt }} | 3.7% |
{% else -%}
!!! info "Economic Data Pending"
    Economic context data will be available after the next BEA/FRED data pipeline run.
{% endif %}

{% if peer_name -%}
## {{ state_name }} vs {{ peer_name }}

| Dimension | {{ state_name }} | {{ peer_name }} |
|-----------|-----------|-----------|
| Income Tax | {{ income_tax_summary }} | {{ peer_income_tax_summary }} |
| Sales Tax | {{ sales_tax_summary }} | {{ peer_sales_tax_summary }} |
| Competitiveness Rank | {{ tf_rank_text or '—' }} | {{ peer_tf_rank_text or '—' }} |

{% endif -%}

{% if history -%}
## Historical Context

{% for event in history -%}
- **{{ event.year }}**: {{ event.event }}
{% endfor %}
{% endif -%}

## Federal Interaction

- **PTET Status**: {{ ptet_text }}
- **Federal Conformity**: {{ conformity_text }}
{% if salt_impact -%}
- **SALT Cap Impact**: {{ salt_impact|capitalize }}
{% endif %}

## Data Sources & Citations

1. Census Bureau, Annual Survey of State Tax Collections (FY2023)
2. Bureau of Economic Analysis, Regional Economic Accounts (2024)
3. Tax Foundation, *State Tax Competitiveness Index* (2024)
4. Tax Foundation, *Facts & Figures* (2025)
5. ITEP, *Who Pays?* (7th Edition, 2024)

---

<div class="source-note" markdown>
All data verified against primary sources. See [Methodology](../methodology/index.md) for full documentation of data sources and analytical approach.
</div>
"""


def _get_income_tax_summary(abbr: str, ts: dict | None) -> str:
    """One-line income tax summary for comparison tables."""
    if abbr in NO_INCOME_TAX:
        return "None"
    if not ts:
        return "Data pending"
    brackets = ts.get("income_tax_brackets", [])
    itype = ts.get("income_tax_type", "")
    if not brackets:
        return itype.capitalize() if itype else "Data pending"
    rates = [b.get("rate", 0) for b in brackets]
    if len(set(rates)) == 1:
        return f"Flat {rates[0]}%"
    return f"Graduated ({min(rates)}%\u2013{max(rates)}%)"


def _get_sales_tax_summary(ts: dict | None) -> str:
    """One-line sales tax summary."""
    if not ts:
        return "Data pending"
    rate = ts.get("sales_tax_rate")
    if rate is None:
        return "Data pending"
    local = ts.get("local_sales_tax")
    suffix = " (+ local)" if local else " (no local)" if local is False else ""
    return f"{rate}%{suffix}"


def generate_state_page(
    abbr: str,
    profile: dict,
    ref_data: dict,
    history_data: dict,
    tf_ref: dict,
    env: Environment,
) -> str:
    """Generate markdown content for a single state."""
    name = STATE_NAMES.get(abbr, "")
    ts = profile.get("tax_structure") or {}
    ci = profile.get("competitiveness_index") or {}
    kf = profile.get("key_facts") or {}
    econ = profile.get("economic_context") or {}
    brackets = ts.get("income_tax_brackets", [])

    # Format bracket ranges for the table
    formatted_brackets = []
    for b in brackets:
        bmin = b.get("min", 0)
        bmax = b.get("max")
        if bmax is None:
            range_str = f"Over ${bmin:,.0f}"
        else:
            range_str = f"${bmin:,.0f} \u2013 ${bmax:,.0f}"
        formatted_brackets.append({"range": range_str, "rate": b.get("rate", 0)})

    # Estate tax text
    estate_tax = ts.get("estate_tax")
    exemption = ts.get("estate_tax_exemption")
    if estate_tax is True and exemption:
        estate_text = f"Yes \u2014 ${exemption:,.0f} exemption"
    elif estate_tax is True:
        estate_text = "Yes"
    elif estate_tax is False:
        estate_text = "None"
    else:
        estate_text = "Data pending"

    # Notable credits
    credits_list = ts.get("notable_credits", [])
    credits_text = ", ".join(credits_list) if credits_list else "Data pending"

    # PTET and conformity
    ptet = kf.get("ptet_adopted")
    if ptet is True:
        ptet_text = "Adopted \u2014 pass-through entity tax available"
    elif ptet is False:
        ptet_text = "Not adopted"
    else:
        ptet_text = "Data pending"

    conformity = kf.get("federal_conformity")
    if conformity:
        conformity_text = f"{conformity.capitalize()} conformity to IRC"
    else:
        conformity_text = "Data pending"

    # Economic context formatting
    econ_fmt = {}
    for key in ("median_household_income", "per_capita_income", "gdp_per_capita"):
        val = econ.get(key)
        econ_fmt[f"{key}_fmt"] = _format_currency(val) if val else "\u2014"
    ur = econ.get("unemployment_rate")
    econ_fmt["unemployment_rate_fmt"] = f"{ur}%" if ur else "\u2014"

    # Tax Foundation rank
    overall_rank = ci.get("overall_rank")
    tf_rank_text = _ordinal(overall_rank) if overall_rank else None

    # Peer comparison
    peer_abbr = STATE_PEERS.get(abbr)
    peer_name = STATE_NAMES.get(peer_abbr, "") if peer_abbr else None
    peer_ts = None
    peer_ci = None
    peer_tf_rank_text = None
    if peer_abbr:
        peer_ref = ref_data.get(peer_abbr, ref_data.get("_template", {}))
        peer_ts = peer_ref.get("tax_structure")
        peer_tf = tf_ref.get("states", {}).get(peer_abbr, {})
        peer_rank = peer_tf.get("overall_rank")
        peer_tf_rank_text = _ordinal(peer_rank) if peer_rank else None

    # History
    history = history_data.get(abbr, [])

    # SALT impact
    salt_impact = kf.get("salt_impact")

    # Build context
    template = env.from_string(TEMPLATE)
    return template.render(
        state_name=name,
        abbr=abbr,
        abbr_lower=abbr.lower(),
        overview=_build_overview(abbr, profile, ci),
        glance_cards=_build_glance_cards(abbr, profile),
        no_income_tax=abbr in NO_INCOME_TAX,
        has_brackets=bool(brackets),
        brackets=formatted_brackets,
        property_tax_admin=ts.get("property_tax_admin"),
        estate_tax_text=estate_text,
        notable_credits=credits_text,
        ptet_text=ptet_text,
        conformity_text=conformity_text,
        has_revenue_data=profile.get("revenue_composition") is not None,
        has_itep_data=profile.get("effective_rates_by_quintile") is not None,
        itep_partial=bool((profile.get("effective_rates_by_quintile") or {}).get("_partial")),
        has_tf_data=overall_rank is not None,
        tf_rank_text=tf_rank_text,
        is_progressive=abbr in ITEP_PROGRESSIVE,
        is_regressive=abbr in ITEP_MOST_REGRESSIVE,
        has_economic_data=bool(econ),
        econ=econ_fmt,
        income_tax_summary=_get_income_tax_summary(abbr, ts),
        sales_tax_summary=_get_sales_tax_summary(ts),
        peer_name=peer_name,
        peer_income_tax_summary=_get_income_tax_summary(peer_abbr, peer_ts) if peer_abbr else "",
        peer_sales_tax_summary=_get_sales_tax_summary(peer_ts) if peer_abbr else "",
        peer_tf_rank_text=peer_tf_rank_text,
        history=history,
        salt_impact=salt_impact,
    )


def _generate_index(profiles: dict[str, dict], tf_ref: dict, itep_ref: dict) -> str:
    """Generate the states/index.md page with all 50 states."""
    rows = []
    for abbr in sorted(STATE_FIPS.keys()):
        name = STATE_NAMES.get(abbr, "")
        slug = _state_slug(name)

        # Income tax type
        if abbr in NO_INCOME_TAX:
            income = "None"
        elif abbr in FLAT_TAX:
            income = "Flat"
        else:
            income = "Graduated"

        # Sales tax
        profile = profiles.get(abbr, {})
        ts = profile.get("tax_structure") or {}
        sales_rate = ts.get("sales_tax_rate")
        sales = f"{sales_rate}%" if sales_rate else "\u2014"

        # Competitiveness rank
        tf = tf_ref.get("states", {}).get(abbr, {})
        rank = tf.get("overall_rank")
        rank_text = _ordinal(rank) if rank else "\u2014"

        # ITEP assessment
        if abbr in ITEP_PROGRESSIVE:
            itep = "Progressive"
        elif abbr in ITEP_MOST_REGRESSIVE:
            itep = "Most regressive"
        else:
            itep = "\u2014"

        rows.append(
            f"| {name} | {income} | {sales} | {rank_text} | {itep} | "
            f"[View]({slug}.md) |"
        )

    table = "\n".join(rows)

    return f"""# State Tax Structure Profiles

Tax Structure Watch provides comprehensive tax structure profiles for every state. Each profile includes revenue composition, distributional analysis from competing frameworks, historical context, and federal interaction data.

## All State Profiles

| State | Income Tax | Sales Tax | Competitiveness Rank | ITEP Assessment | Profile |
|-------|-----------|-----------|---------------------|-----------------|---------|
{table}

## The 50-State Landscape

### By Income Tax Structure (as of 2026)

**No Income Tax (9 states)**: Alaska, Florida, Nevada, New Hampshire[^1], South Dakota, Tennessee, Texas, Washington, Wyoming

**Flat Rate (15 states)**: Arizona, Colorado, Georgia, Idaho, Illinois, Indiana, Iowa, Kentucky, Michigan, Mississippi, Montana, North Carolina, North Dakota, Pennsylvania, Utah

**Graduated Rates (26 states + DC)**: Alabama, Arkansas, California, Connecticut, Delaware, Hawaii, Kansas, Louisiana, Maine, Maryland, Massachusetts, Minnesota, Missouri, Nebraska, New Jersey, New Mexico, New York, Ohio, Oklahoma, Oregon, Rhode Island, South Carolina, Vermont, Virginia, West Virginia, Wisconsin, plus DC

[^1]: New Hampshire taxes interest and dividends income only, which is being phased out.

!!! info "The Flat Tax Revolution"
    Since 2021, eight states have converted from graduated to flat income tax structures, and several more have enacted triggers to reduce or eliminate their income taxes over time. This is the most significant structural transformation in state taxation in decades. [Read our analysis \u2192](../analysis/flat-tax-revolution.md)

### By Distributional Impact (ITEP)

**Most Regressive** (highest effective rates on lowest-income households): Florida, Washington, Tennessee, Pennsylvania, Nevada, South Dakota, Texas, Illinois, Arkansas, Louisiana

**Most Progressive** (6 states + DC that reduce inequality): California, Maine, Minnesota, New Jersey, New York, Vermont, DC

---

<div class="source-note" markdown>
**Sources**: Tax Foundation, *Facts & Figures* (2025); ITEP, *Who Pays?* (7th Edition); Census Bureau, Annual Survey of State Tax Collections. State profiles updated as new data becomes available.
</div>
"""


def generate_all_pages(state_filter: str | None = None) -> dict[str, str]:
    """
    Generate markdown pages for all states (or single state).

    Returns dict of abbr -> file path of generated pages.
    """
    ensure_dirs()
    os.makedirs(STATES_DIR, exist_ok=True)

    env = Environment(
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )

    # Load reference data
    ref_data = load_json(os.path.join(REFERENCE_DIR, "state_tax_structures.json")) or {}
    history_data = load_json(os.path.join(REFERENCE_DIR, "state_tax_history.json")) or {}
    tf_ref = load_json(os.path.join(REFERENCE_DIR, "tax_foundation_index.json")) or {}
    itep_ref = load_json(os.path.join(REFERENCE_DIR, "itep_whopays.json")) or {}

    states = [state_filter.upper()] if state_filter else sorted(STATE_FIPS.keys())
    generated = {}

    # Build profile data for all states (for index generation)
    all_profiles = {}
    for abbr in sorted(STATE_FIPS.keys()):
        profile_path = os.path.join(SITE_DIR, f"{abbr.lower()}_profile.json")
        profile = load_json(profile_path)
        if profile:
            all_profiles[abbr] = profile
        else:
            # Build minimal profile from reference data
            state_ref = ref_data.get(abbr, ref_data.get("_template", {}))
            all_profiles[abbr] = {
                "state": STATE_NAMES.get(abbr, ""),
                "abbreviation": abbr,
                "tax_structure": state_ref.get("tax_structure"),
                "competitiveness_index": tf_ref.get("states", {}).get(abbr),
                "key_facts": state_ref.get("key_facts"),
            }

    for abbr in states:
        if abbr not in STATE_FIPS:
            logger.warning("Unknown state abbreviation: %s — skipping", abbr)
            continue

        name = STATE_NAMES.get(abbr, "")
        slug = _state_slug(name)
        out_path = os.path.join(STATES_DIR, f"{slug}.md")

        # Skip hand-authored WI and MN pages
        if abbr in ("WI", "MN") and os.path.exists(out_path):
            logger.info("Skipping %s — hand-authored page exists at %s", abbr, out_path)
            continue

        profile = all_profiles.get(abbr, {})

        content = generate_state_page(
            abbr, profile, ref_data, history_data, tf_ref, env,
        )

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        generated[abbr] = out_path
        logger.info("Generated %s -> %s", abbr, out_path)

    # Regenerate index
    index_content = _generate_index(all_profiles, tf_ref, itep_ref)
    index_path = os.path.join(STATES_DIR, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    logger.info("Regenerated states/index.md")

    # Output nav snippet to stdout
    print("\n--- mkdocs.yml nav snippet (States section) ---")
    print("  - States:")
    print("    - Overview: states/index.md")
    for abbr in sorted(STATE_FIPS.keys()):
        name = STATE_NAMES.get(abbr, "")
        slug = _state_slug(name)
        print(f"    - {name}: states/{slug}.md")
    print("--- end nav snippet ---\n")

    logger.info("Generated %d state page(s)", len(generated))
    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate state profile markdown pages")
    parser.add_argument(
        "--state", type=str, default=None,
        help="Generate page for a single state (e.g., CA)",
    )
    args = parser.parse_args()
    generate_all_pages(state_filter=args.state)
