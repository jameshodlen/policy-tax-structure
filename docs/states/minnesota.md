# Minnesota Tax Structure

> **Last updated**: March 2026 | **Data sources**: Census Bureau, BEA, IRS SOI, ITEP, Tax Foundation, Minnesota DOR

## Overview

Minnesota employs one of the most progressive state tax systems in the country — a graduated individual income tax with a top rate of 9.85%, a 6.875% sales tax with a clothing exemption, a 9.8% corporate tax rate, and an estate tax. Minnesota is one of only six states (plus DC) that ITEP identifies as reducing income inequality through its tax code.

This progressivity comes at a competitive cost by Tax Foundation metrics: Minnesota ranks 45th on the State Tax Competitiveness Index. The state represents one side of the fundamental trade-off in state tax policy — distributional equity vs. competitive positioning — and is a critical case study for understanding what the data can and cannot tell us about the consequences of that choice.

## Tax Structure at a Glance

<div class="tax-glance" markdown>
<div class="card" markdown>
<div class="label">Income Tax</div>
<div class="value">5.35%–9.85%</div>
<div class="detail">4 brackets, graduated</div>
</div>
<div class="card" markdown>
<div class="label">Sales Tax</div>
<div class="value">6.875%</div>
<div class="detail">Clothing exempt, local add-ons</div>
</div>
<div class="card" markdown>
<div class="label">Corporate Tax</div>
<div class="value">9.8%</div>
<div class="detail">Single rate</div>
</div>
<div class="card" markdown>
<div class="label">Competitiveness</div>
<div class="value">#45</div>
<div class="detail">Tax Foundation Index</div>
</div>
</div>

### Income Tax Brackets (Single Filer, 2025)

| Taxable Income | Rate |
|---------------|------|
| $0 – $31,690 | 5.35% |
| $31,690 – $104,090 | 6.80% |
| $104,090 – $193,240 | 7.85% |
| Over $193,240 | 9.85% |

### Other Key Features

| Category | Detail |
|----------|--------|
| **Property Tax** | Locally assessed with state-paid property tax refund (circuit breaker). Classify property types with different rates |
| **Estate Tax** | Yes — $3 million exemption, graduated rates 13%–16% |
| **Notable Credits** | Working Family Credit (state EITC), K-12 Education Credit, Child Tax Credit, Property Tax Refund |
| **Sales Tax Exemptions** | Clothing, food (grocery), prescription drugs, most services |
| **PTET Status** | Adopted — pass-through entity tax available |
| **Federal Conformity** | Selective — Minnesota selectively conforms to IRC changes |

## Revenue Composition

How Minnesota generates its state tax revenue, by source:

<div class="chart-container" markdown>
<canvas data-chart-type="pie"
        data-source="../assets/data/mn_profile.json"
        data-key="revenue_composition">
</canvas>
</div>

!!! note "What this shows"
    Minnesota relies heavily on individual income taxes (53%) — the highest income tax share among peer states. Sales taxes (22%) are lower than the national average despite the relatively high 6.875% rate, partly because Minnesota exempts clothing and most services. Corporate income taxes contribute 8% of revenue.

## Who Pays? Effective Tax Rates by Income

<div class="chart-container" markdown>
<canvas data-chart-type="bar"
        data-source="../assets/data/mn_profile.json"
        data-key="effective_rates_by_quintile">
</canvas>
</div>

=== "Tax Foundation View"

    Minnesota ranks **45th** on the State Tax Competitiveness Index (2024). Key assessments:

    - **Individual Income Tax (46th)**: The 9.85% top rate is the 6th highest in the nation. Four brackets add complexity.
    - **Sales Tax (31st)**: The 6.875% rate is above average, but the clothing exemption narrows the base unnecessarily.
    - **Property Tax (28th)**: Minnesota's classification system and property tax refund add complexity but moderate effective burdens.
    - **Corporate Tax (47th)**: The 9.8% rate is among the highest nationally.

    The Tax Foundation would note that Minnesota's high rates on both individual and corporate income create competitive disadvantages, particularly as neighboring states (Iowa, North Dakota) have moved to lower, flatter structures.

=== "ITEP View"

    Minnesota is one of only **six states plus DC** whose tax system **reduces income inequality**. ITEP's analysis shows:

    - The **lowest-income 20%** pay approximately 8.7% of their income in state and local taxes
    - The **top 1%** pay approximately 12.3%
    - This is one of the few states where the effective rate *increases* with income

    Minnesota achieves this through a combination of graduated income tax rates, a robust Working Family Credit (state EITC), property tax refunds targeted at lower-income homeowners and renters, and sales tax exemptions on necessities (clothing, food).

=== "Primary Source Data"

    From Census Bureau and IRS SOI data:

    - **Total state tax collections** (FY2023): ~$27.5 billion
    - **Per capita tax burden**: ~$4,820
    - **As % of personal income**: ~10.6%
    - **Median household income**: ~$80,441

    Minnesota has among the highest per-capita tax burdens nationally and also among the highest median incomes. The tax-to-income ratio (10.6%) is above the national average but not dramatically so.

## Economic Context

| Metric | Minnesota | National Median |
|--------|-----------|----------------|
| Median Household Income | $80,441 | $74,580 |
| Per Capita Income | $42,500 | $37,638 |
| GDP Per Capita | $68,200 | $63,444 |
| Unemployment Rate | 2.9% | 3.7% |
| Population | 5,717,184 | — |

## Minnesota vs Wisconsin

Minnesota and Wisconsin are the platform's anchor comparison — neighboring Midwestern states with divergent tax philosophies.

| Dimension | Minnesota | Wisconsin |
|-----------|-----------|-----------|
| Income Tax Structure | Graduated, 4 brackets (5.35%–9.85%) | Graduated, 4 brackets (3.5%–7.65%) |
| Top Marginal Rate | 9.85% | 7.65% |
| Sales Tax | 6.875% (clothing exempt, + local) | 5.0% (no local) |
| Corporate Tax | 9.8% | 7.9% |
| Estate Tax | Yes ($3M exemption) | None |
| Competitiveness Rank | 45th | 28th |
| ITEP Assessment | Progressive (reduces inequality) | Moderately regressive |
| Median Household Income | $80,441 | $67,125 |
| Unemployment Rate | 2.9% | 3.1% |

!!! question "Does higher taxation cause higher or lower prosperity?"
    This is the central question that the Wisconsin-Minnesota comparison raises — and one the data cannot definitively answer. Minnesota has higher tax rates *and* higher incomes. Multiple interpretations are defensible:

    **Interpretation A (center-right)**: Minnesota succeeds *despite* its high taxes, not because of them. Its economic advantages (Fortune 500 concentration, healthcare sector, higher educational attainment) would produce even stronger results with a more competitive tax structure.

    **Interpretation B (center-left)**: Minnesota's progressive tax structure *enables* the public investments (education, infrastructure, healthcare) that produce its economic outcomes. The tax structure is an input to prosperity, not a drag on it.

    **What the data cannot tell us**: Cross-state comparisons cannot isolate the causal effect of tax policy from the many other factors that differ between states. See [Limitations](../methodology/limitations.md).

## Historical Context

- **1933**: Individual income tax enacted (one of the earliest states)
- **1967**: Sales tax enacted at 3%, gradually raised to 6.875%
- **1991**: Fourth income tax bracket added (8.5% on high earners)
- **2013**: Top rate raised to 9.85% on income over ~$156,000 (adjusted annually)
- **2014**: Working Family Credit expanded
- **2023**: Major tax bill — Child Tax Credit enacted, additional property tax refund, K-12 credit expanded
- **PTET adopted**: Pass-through entity tax enacted as SALT cap workaround

## Federal Interaction

- **SALT Cap Impact**: Significant. Minnesota's high income and property taxes mean many residents previously deducted well above $10,000 in state and local taxes. The SALT cap disproportionately affects Minnesota's upper-middle-income households.
- **PTET Status**: Adopted. Available for qualifying pass-through entities.
- **Federal Conformity**: Selective. Minnesota maintains its own tax code with selective conformity to federal changes, creating potential complexity when federal law changes.
- **Estate Tax Interaction**: Minnesota's $3 million estate tax exemption is well below the federal exemption (~$13.6 million), creating a state-level estate tax obligation for estates that owe nothing federally.

## Data Sources & Citations

1. Census Bureau, Annual Survey of State Tax Collections (FY2023)
2. Bureau of Economic Analysis, Regional Economic Accounts (2024)
3. IRS Statistics of Income, State Data (Tax Year 2022)
4. Tax Foundation, *State Tax Competitiveness Index* (2024)
5. Tax Foundation, *Facts & Figures* (2025)
6. ITEP, *Who Pays?* (6th Edition, 2018)
7. Minnesota Department of Revenue, *Tax Incidence Study* (2023)
8. Minnesota Department of Revenue, *Tax Expenditure Budget* (2024)

---

<div class="source-note" markdown>
All data verified against primary sources. Effective tax rates are estimates based on ITEP modeling and Minnesota DOR Tax Incidence Study. Individual experiences will vary. See [Methodology](../methodology/index.md) for full documentation.
</div>
