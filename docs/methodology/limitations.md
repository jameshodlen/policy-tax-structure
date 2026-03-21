# Limitations: What the Data Can and Cannot Tell Us

Every dataset and every analytical framework has limitations. Transparency about those limitations is as important as the data itself. This page documents what our data can and cannot tell us.

## Data Lag

| Source | Typical Lag | Impact |
|--------|------------|--------|
| Census Annual Tax Collections | 18-24 months | The most recent complete annual data is always at least a year old |
| Census Quarterly Estimates | ~1 quarter | Faster but less detailed than annual data |
| IRS Statistics of Income | ~2 years | Income distribution and migration data reflects conditions from two years prior |
| BEA State Personal Income | 1-2 quarters | Economic context is reasonably current |
| ITEP Who Pays? | Variable (last full edition: 2018) | Distributional analysis may not reflect recent tax law changes |
| Tax Foundation Index | ~1 year | Updated annually with most current law |

!!! warning "Rate changes may not be reflected"
    When a state enacts a major tax change (e.g., converting from graduated to flat income tax), there can be a multi-year gap before the distributional impact appears in the data. We note pending changes in state profiles where applicable.

## Missing Data

### Tax Expenditures

Tax expenditures — revenue forgone through exemptions, credits, deductions, and preferential rates — are the "hidden budget" of state tax policy. Data quality varies dramatically:

- Some states publish comprehensive tax expenditure reports (e.g., Minnesota, California)
- Some publish partial reports
- Some publish nothing at all

Where tax expenditure data is unavailable, we cannot assess the full distributional impact of a state's tax code. We note data availability in each state profile.

### Local Taxes

This platform focuses primarily on state-level taxes. Local taxes (county, municipal, special district) add significant complexity:

- 17 states permit local income taxes
- Combined state + local sales tax rates vary within states
- Property taxes are administered locally with enormous variation

We incorporate local tax data where available (primarily from Tax Foundation combined rate data and Lincoln Institute property tax studies) but coverage is incomplete. The effective rates reported in state profiles are state-level unless otherwise noted.

### Informal Economy

All tax data measures the formal, reported economy. Underground economic activity, unreported cash income, and tax evasion are not captured. This affects comparisons between states with different economic structures and enforcement regimes.

## Analytical Limitations

### Correlation vs Causation

This platform presents correlations — relationships between tax structures and economic or social outcomes. **Correlation does not establish causation.** When we show that states without income taxes have different migration patterns than states with high income taxes, we are showing a correlation. The migration may be caused by:

- Tax rate differentials
- Job market differences
- Housing costs
- Climate preferences
- Remote work adoption
- Or any combination of factors

We present the correlation data honestly and note competing causal interpretations. We do not claim to have identified the "true" cause of complex economic phenomena.

### Confounding Variables

State-level comparisons are inherently confounded. States differ in:

- Economic structure (oil states vs. service economies vs. manufacturing)
- Demographic composition
- Geographic factors (coastal vs. inland, urban vs. rural mix)
- Historical development patterns
- Federal funding levels and military presence

Any comparison that attributes outcomes solely to tax policy is oversimplified. We provide economic context data (BEA) to help users understand these confounders, but we cannot fully control for them.

### Incidence Uncertainty

Who actually bears the burden of a tax is an open question in public finance. Reasonable economists disagree about:

- How much of the corporate income tax falls on shareholders vs. workers vs. consumers
- Whether property taxes are borne by landowners or passed through to tenants
- Whether sales tax burdens are shifted through wage adjustments

Different assumptions about incidence produce different distributional conclusions. This is one of the core reasons the Tax Foundation and ITEP reach different results (see [Tax Foundation vs ITEP](tax-foundation-vs-itep.md)).

### Small Sample Sizes

Some data (particularly IRS SOI migration data for small states or specific income brackets) involves small sample sizes. We note when sample sizes are small enough to raise reliability concerns.

## What We Cannot Do

1. **Predict the future** — We do not forecast what will happen if a state changes its tax structure. We can show what has happened historically in similar situations, but prediction requires causal models that the data does not support.

2. **Declare a "winner"** — We do not rank states as having "good" or "bad" tax systems. Both the Tax Foundation and ITEP offer rankings based on their respective frameworks. We present both without endorsing either.

3. **Account for all public revenue** — Taxes are not the only source of state revenue. Federal grants, fees, fines, investment returns, and lottery revenue all contribute. We note non-tax revenue where relevant but do not comprehensively model it.

4. **Measure tax system outcomes in isolation** — A state's education quality, infrastructure condition, or healthcare access depends on far more than its tax structure. We present outcome data as context, not as evidence of tax policy success or failure.
