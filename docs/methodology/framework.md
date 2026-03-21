# Analytical Framework

## What We Measure

Tax Structure Watch examines state tax systems across three dimensions:

### 1. Revenue Composition

**What sources does a state rely on to fund government services?**

We decompose each state's tax revenue into its component parts using Census Bureau Annual Survey of State Tax Collections data:

- Individual income tax
- Corporate income tax
- General sales tax
- Selective sales taxes (motor fuel, alcohol, tobacco, insurance premiums)
- Property taxes (state-administered portion)
- License taxes
- Severance taxes
- Other taxes

This revenue mix matters because different tax types have different distributional properties. A state that relies heavily on sales taxes places a proportionally larger burden on lower-income households (who spend a higher share of income on taxable goods) than a state that relies on graduated income taxes.

### 2. Distributional Impact

**Who bears the actual burden of a state's tax system?**

This is the most contested question in state tax policy, and the one where competing frameworks diverge most sharply. We present two primary analyses:

- **ITEP Who Pays?** — Calculates effective state and local tax rates by income quintile, finding that most state tax systems are regressive (lower-income households pay a higher effective rate)
- **Tax Foundation State Tax Competitiveness Index** — Evaluates state tax structures on neutrality, simplicity, transparency, and stability, ranking states on how well their tax codes promote economic growth

These frameworks ask fundamentally different questions and reach fundamentally different conclusions. We present both, explain their assumptions, and let users evaluate. See [Tax Foundation vs ITEP](tax-foundation-vs-itep.md) for a detailed comparison.

### 3. Economic Context

**What is the broader economic environment in which a state's tax system operates?**

Tax data is meaningless without economic context. We use Bureau of Economic Analysis data to provide:

- **State personal income** — The standard baseline for effective tax burden calculations
- **GDP by state** — Total economic output
- **Regional price parities** — Cost-of-living adjustments that affect real tax burden comparisons
- **Employment and industry mix** — Structural factors that shape a state's revenue capacity

## How We Calculate

### Effective Tax Rates

We report effective tax rates (total tax paid as a percentage of income) rather than statutory rates (the rate written into law). Effective rates account for deductions, credits, exemptions, and the interaction between tax types. They answer the question "what do people actually pay?" rather than "what does the law say the rate is?"

### Per-Capita Normalization

Raw revenue totals are normalized to per-capita figures using Census Bureau population estimates. This allows meaningful comparison between states of vastly different sizes.

### Income-Adjusted Burden

We calculate tax burden as a percentage of state personal income (from BEA) to account for differences in income levels across states. A state with $2,000 per-capita tax revenue has a very different burden depending on whether per-capita income is $40,000 or $80,000.

## Data Pipeline

All data flows through a documented pipeline:

```
Primary Source APIs → Raw Data → Processing & Validation → State Profiles → Site JSON
(Census, BEA, IRS)   (data/raw/)  (data/processed/)       (build_state_profiles.py)
```

Each step is logged, validated, and reproducible. See the [Data Sources](../data/index.md) directory for the complete list of sources and their update frequencies.
