# Data

Raw and processed datasets from public sources.

## Directory Structure

- `raw/` — Raw API responses and downloaded files (gitignored)
- `processed/` — Cleaned, normalized JSON ready for analysis (gitignored)

Site-ready JSON files are output to `docs/assets/data/` for MkDocs to serve.

## Sources

- Census Bureau State Tax Collections (API)
- Bureau of Economic Analysis Regional Data (API)
- FRED Economic Series (API)
- Treasury Fiscal Data (API)
- IRS Statistics of Income (file download)
- Tax Foundation Facts & Figures (file download)
- ITEP Who Pays? (file download)
- Lincoln Institute Property Tax Data (file download)

## Pipeline

See `../scripts/` for automated ingestion and processing scripts.
Run `python scripts/run_pipeline.py` from the project root.
