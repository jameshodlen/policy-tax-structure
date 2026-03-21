# Wisconsin Tax Structure

> **Last updated**: March 2026 | **Data sources**: Census Bureau, BEA, IRS SOI, ITEP, Tax Foundation, Wisconsin DOR

## Overview

Wisconsin employs a graduated individual income tax with four brackets, a 5% state sales tax with no local add-on, and heavy reliance on property taxes administered at the local level. The state has maintained its graduated income tax structure through the recent wave of flat tax conversions, though legislative proposals to flatten or reduce rates have been introduced in recent sessions.

Wisconsin's tax system is moderately regressive by ITEP's analysis but less so than the national average, largely because its graduated income tax partially offsets the regressivity of its sales and property taxes. The Tax Foundation ranks Wisconsin 28th on its State Tax Competitiveness Index, with relatively poor marks for property taxes and individual income taxes but a strong sales tax score (due to the single statewide rate with no local taxes).

## Tax Structure at a Glance

<div class="tax-glance" markdown>
<div class="card" markdown>
<div class="label">Income Tax</div>
<div class="value">3.5%–7.65%</div>
<div class="detail">4 brackets, graduated</div>
</div>
<div class="card" markdown>
<div class="label">Sales Tax</div>
<div class="value">5.0%</div>
<div class="detail">No local sales taxes</div>
</div>
<div class="card" markdown>
<div class="label">Corporate Tax</div>
<div class="value">7.9%</div>
<div class="detail">Single rate</div>
</div>
<div class="card" markdown>
<div class="label">Competitiveness</div>
<div class="value">#28</div>
<div class="detail">Tax Foundation Index</div>
</div>
</div>

### Income Tax Brackets (Single Filer, 2025)

| Taxable Income | Rate |
|---------------|------|
| $0 – $14,320 | 3.50% |
| $14,320 – $28,640 | 4.40% |
| $28,640 – $315,310 | 5.30% |
| Over $315,310 | 7.65% |

### Other Key Features

| Category | Detail |
|----------|--------|
| **Property Tax** | Locally assessed, state equalization. High reliance — WI property taxes among highest nationally |
| **Estate Tax** | None (repealed 1992) |
| **Notable Credits** | Homestead Credit, state Earned Income Tax Credit (4%–34% of federal), School Property Tax Credit |
| **Sales Tax Exemptions** | Food (grocery), prescription drugs |
| **PTET Status** | Adopted — pass-through entity tax available as SALT cap workaround |
| **Federal Conformity** | Selective — Wisconsin selectively conforms to IRC changes |

## Revenue Composition

How Wisconsin generates its state tax revenue, by source:

<div class="chart-container" markdown>
<canvas data-chart-type="pie"
        data-source="../assets/data/wi_profile.json"
        data-key="revenue_composition">
</canvas>
</div>

!!! note "What this shows"
    Wisconsin relies heavily on individual income taxes (46%) and sales taxes (27%), with significant property tax revenue flowing through local governments. Corporate income taxes account for roughly 7% of state tax collections.

## Who Pays? Effective Tax Rates by Income

This is the central question — and the one where competing frameworks diverge. Below are effective state and local tax rates by income group, showing what different income levels actually pay as a percentage of their income.

<div class="chart-container" markdown>
<canvas data-chart-type="bar"
        data-source="../assets/data/wi_profile.json"
        data-key="effective_rates_by_quintile">
</canvas>
</div>

=== "Tax Foundation View"

    Wisconsin ranks **28th** on the State Tax Competitiveness Index (2024). Key assessments:

    - **Individual Income Tax (30th)**: The top marginal rate of 7.65% is above the national median. The graduated structure with four brackets adds complexity.
    - **Sales Tax (13th)**: Wisconsin scores well here — the single statewide 5% rate with no local add-ons is simple and transparent.
    - **Property Tax (36th)**: High property tax burdens are a significant competitive disadvantage.
    - **Corporate Tax (35th)**: The 7.9% rate is above the national median.

    The Tax Foundation would note that Wisconsin's graduated income tax and high property taxes create competitive disadvantages relative to neighboring states, particularly as Iowa has moved to a flat tax.

=== "ITEP View"

    Wisconsin's tax system is **moderately regressive** but less so than the national average. ITEP's analysis shows:

    - The **lowest-income 20%** pay approximately 8.9% of their income in state and local taxes
    - The **top 1%** pay approximately 7.7%
    - The spread (1.2 percentage points) is significantly smaller than the national average spread

    Wisconsin's graduated income tax and earned income tax credit partially offset the regressivity of its sales and property taxes. However, the system still asks more (proportionally) of lower-income households than higher-income ones.

=== "Primary Source Data"

    From Census Bureau and IRS SOI data:

    - **Total state tax collections** (FY2023): ~$19.8 billion
    - **Per capita tax burden**: ~$3,360
    - **As % of personal income**: ~9.2%
    - **Median household income**: ~$67,125

    These figures place Wisconsin near the middle of states on total tax effort, with above-average income tax collections and below-average sales tax collections relative to personal income.

## Economic Context

| Metric | Wisconsin | National Median |
|--------|-----------|----------------|
| Median Household Income | $67,125 | $74,580 |
| Per Capita Income | $35,100 | $37,638 |
| GDP Per Capita | $57,800 | $63,444 |
| Unemployment Rate | 3.1% | 3.7% |
| Population | 5,893,718 | — |

## Wisconsin vs Minnesota

Wisconsin and Minnesota are the platform's anchor comparison — neighboring Midwestern states with divergent tax philosophies.

| Dimension | Wisconsin | Minnesota |
|-----------|-----------|-----------|
| Income Tax Structure | Graduated, 4 brackets (3.5%–7.65%) | Graduated, 4 brackets (5.35%–9.85%) |
| Top Marginal Rate | 7.65% | 9.85% |
| Sales Tax | 5.0% (no local) | 6.875% (+ local, clothing exempt) |
| Corporate Tax | 7.9% | 9.8% |
| Estate Tax | None | Yes ($3M exemption) |
| Competitiveness Rank | 28th | 45th |
| ITEP Assessment | Moderately regressive | Progressive (one of 6 states reducing inequality) |
| Median Household Income | $67,125 | $80,441 |

!!! question "What explains the income gap?"
    Minnesota's median household income is approximately $13,000 higher than Wisconsin's despite (or perhaps unrelated to) significantly higher tax rates. This correlation does not establish causation — Minnesota's economic structure (Fortune 500 headquarters, healthcare sector, higher urbanization) differs substantially from Wisconsin's. See our [methodology](../methodology/limitations.md) on correlation vs causation.

## Historical Context

- **1911**: Wisconsin becomes one of the first states to adopt an individual income tax
- **1962**: Sales tax enacted at 3%, raised to 5% in 1982
- **1992**: Estate tax repealed
- **2011–2015**: Significant tax cuts under Governor Walker, including income tax rate reductions
- **2023–2025**: Legislative proposals to flatten income tax to single rate; none enacted as of early 2026
- **PTET adopted**: Pass-through entity tax enacted as SALT cap workaround

## Federal Interaction

- **SALT Cap Impact**: Moderate. Wisconsin's high property taxes mean many homeowners previously deducted significant state and local taxes. The $10,000 SALT cap (raised to $40,000 under OBBBA but phased out at $500,000 AGI) affects upper-middle-income households.
- **PTET Status**: Adopted. Business owners can elect pass-through entity taxation to circumvent the individual SALT cap.
- **Federal Conformity**: Selective. Wisconsin reviews and selectively adopts IRC changes rather than auto-conforming.

## Data Sources & Citations

1. Census Bureau, Annual Survey of State Tax Collections (FY2023)
2. Bureau of Economic Analysis, Regional Economic Accounts (2024)
3. IRS Statistics of Income, State Data (Tax Year 2022)
4. Tax Foundation, *State Tax Competitiveness Index* (2024)
5. Tax Foundation, *Facts & Figures* (2025)
6. ITEP, *Who Pays?* (6th Edition, 2018)
7. Wisconsin Department of Revenue, *Blue Book* (2024)

---

<div class="source-note" markdown>
All data verified against primary sources. Effective tax rates are estimates based on ITEP modeling and may differ from individual experiences. See [Methodology](../methodology/index.md) for full documentation of data sources and analytical approach.
</div>
