# Data Sources

Tax Structure Watch uses exclusively primary-source data, supplemented by two analytical frameworks (Tax Foundation and ITEP) whose methodologies we document transparently. This page catalogs every data source, its access method, update frequency, and any known limitations.

## Tier 1: API Sources (Automated Pipeline)

These sources have programmatic APIs. Our data pipeline fetches, processes, and validates this data automatically.

| Source | Type | API | Frequency | Key Data | Lean |
|--------|------|-----|-----------|----------|------|
| [Census State Tax Collections](https://www.census.gov/programs-surveys/stc.html) | Revenue | Yes | Annual + Quarterly | Revenue by category, all 50 states, back to 1939 | Nonpartisan |
| [Bureau of Economic Analysis (BEA)](https://www.bea.gov/data/by-place-state) | Economic context | Yes | Quarterly | Personal income, GDP by state, regional price parities | Nonpartisan |
| [FRED (St. Louis Fed)](https://fred.stlouisfed.org/) | Aggregator | Yes | Varies | 812,000+ series mirroring Census + BEA data | Nonpartisan |
| [Treasury Fiscal Data](https://fiscaldata.treasury.gov/) | Federal context | Yes (open) | Monthly | Federal grants to states, Treasury statements | Nonpartisan |

### Census Bureau State Tax Collections

The backbone of the platform. The Census Bureau's Annual Survey of State Tax Collections provides revenue by category (individual income, corporate income, general sales, selective sales, property, license, severance) for all 50 states plus DC. Historical data extends back to 1939. Quarterly estimates are also available.

- **Lag**: 18–24 months on annual data; ~1 quarter on quarterly estimates
- **Pipeline script**: `scripts/fetch_census_tax.py`
- **API key**: Required (free) — [Request here](https://api.census.gov/data/key_signup.html)

### Bureau of Economic Analysis (BEA)

Provides the economic denominator — tax data is meaningless without income and GDP context. We use BEA regional data for state personal income (the standard baseline for effective tax burden calculations), GDP by state, and regional price parities (cost-of-living adjustment).

- **Lag**: 1–2 quarters
- **Pipeline script**: `scripts/fetch_bea_regional.py`
- **API key**: Required (free) — [Request here](https://apps.bea.gov/API/signup/)

### FRED (Federal Reserve Bank of St. Louis)

A single programmatic interface to data that otherwise requires navigating multiple agency websites. We use FRED primarily as a cross-check and for time series that are easier to access through FRED's unified API.

- **Pipeline script**: `scripts/fetch_fred_series.py`
- **API key**: Required (free) — [Request here](https://fred.stlouisfed.org/docs/api/api_key.html)

### Treasury Fiscal Data

Federal transfers to states compensate for low state taxes — this data contextualizes the full fiscal picture. We calculate federal dependency ratios to show how much of each state's fiscal capacity comes from federal sources.

- **Lag**: ~1 month
- **Pipeline script**: `scripts/fetch_treasury_fiscal.py`
- **API key**: Not required (open API)

---

## Tier 2: Structured File Downloads (Manual Pipeline)

These sources publish data as downloadable files (CSV, XLSX). Our pipeline downloads and processes them, but new releases must be manually monitored.

| Source | Type | API | Frequency | Key Data | Lean |
|--------|------|-----|-----------|----------|------|
| [IRS Statistics of Income](https://www.irs.gov/statistics) | Returns + Migration | No | Annual (~2yr lag) | Income brackets, deductions, AGI migration | Nonpartisan |
| [Tax Foundation](https://taxfoundation.org/) | Rates + Rankings | No | Annual | Facts & Figures, Competitiveness Index | Center-right |
| [ITEP Who Pays?](https://itep.org/whopays/) | Distributional | No | Periodic | Effective rates by quintile, inequality index | Center-left |
| [Lincoln Institute](https://www.lincolninst.edu/) | Property tax | No | Annual | Effective rates, 100+ cities, 50 rural areas | Nonpartisan |
| [NASBO](https://www.nasbo.org/) | State spending | No | Annual | Expenditures by function | Nonpartisan |

### IRS Statistics of Income (SOI)

State-level returns data by income bracket, including AGI, taxable income, tax liability, deductions (including SALT), and credits. The migration data — county-to-county address changes with aggregate AGI movement — is uniquely valuable for analyzing the relationship between tax policy and migration.

- **Lag**: ~2 years
- **Key datasets**: State-level returns, county-to-county migration flows

### Tax Foundation

The primary center-right analytical framework. Key datasets include Facts & Figures (40+ measures, annually since 1941), the State Tax Competitiveness Index (150+ variables), and state-by-state rate tables.

- **How we use it**: Rankings, rate comparisons, and as one of two competing analytical frameworks
- **What to watch for**: The Competitiveness Index measures a specific definition of "good" tax policy (neutral, simple, broad-based) that prioritizes economic efficiency over distributional equity

### ITEP Who Pays?

The primary center-left analytical framework. Calculates effective state and local tax rates by income quintile for all 50 states, producing a Tax Inequality Index that measures how much each state's tax system increases or decreases income inequality.

- **How we use it**: Distributional analysis, effective rate comparisons, and as one of two competing analytical frameworks
- **What to watch for**: The 6th Edition (2018) is the most recent full analysis. Some state tax structures have changed significantly since publication. ITEP excludes retirees and corporate tax incidence from individual burden calculations.

### Lincoln Institute of Land Policy

The 50-State Property Tax Comparison Study provides effective property tax rates for residential, commercial, industrial, and apartment properties across 100+ cities and 50 rural municipalities. Essential for understanding the tax that funds most local services.

### NASBO State Expenditure Report

Connects tax revenue to service delivery by showing state spending by function (education, healthcare, infrastructure, public safety). This helps answer "what happens next?" — where does the tax revenue go?

---

## Tier 3: Manual Collection (Ongoing)

| Source | Type | Frequency | Notes |
|--------|------|-----------|-------|
| State revenue departments | Primary rates/rules | Ongoing | 50 separate sources, varying quality |
| [Federation of Tax Administrators](https://www.taxadmin.org/) | Current rates | Ongoing | Aggregated rate tables across tax types |
| [Tax Policy Center](https://www.taxpolicycenter.org/) (Urban/Brookings) | Research | Quarterly+ | SLF Data Query, policy briefs (center-left) |
| LegiScan | Legislation | Real-time | Pending tax reform bills in all 50 states |
| State tax expenditure reports | Tax expenditures | Annual (varies) | Quality varies dramatically — see [ITEP directory](https://itep.org/state-by-state-tax-expenditure-reports/) |

---

## Data Pipeline Status

Our automated pipeline runs the following scripts in sequence:

| Script | Source | Status |
|--------|--------|--------|
| `fetch_census_tax.py` | Census Bureau | Ready (requires API key) |
| `fetch_bea_regional.py` | BEA | Ready (requires API key) |
| `fetch_fred_series.py` | FRED | Ready (requires API key) |
| `fetch_treasury_fiscal.py` | Treasury | Ready (open API) |
| `build_state_profiles.py` | All processed data | Ready |

Run the full pipeline: `python scripts/run_pipeline.py`

See the [GitHub repository](https://github.com/jameshodlen/policy-tax-structure) for pipeline source code and documentation.

---

<div class="source-note" markdown>
Data source assessments current as of March 2026. API availability and endpoints may change. File this page as a living document — we update it as sources change.
</div>
