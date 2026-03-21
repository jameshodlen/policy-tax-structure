"""
Pipeline orchestrator for the tax structure research platform.

Runs all data-fetch scripts in sequence, then builds state profiles.
Provides CLI options to run individual steps or skip fetching.

Usage:
    python -m scripts.run_pipeline                  # full pipeline
    python -m scripts.run_pipeline --skip-fetch     # rebuild profiles only
    python -m scripts.run_pipeline --state CA       # single state
"""

import argparse
import logging
import sys
import time
import traceback

from scripts.utils import ensure_dirs, setup_logging

logger = setup_logging("pipeline.orchestrator")


def _run_step(name: str, func, **kwargs) -> bool:
    """
    Execute a pipeline step, logging timing and catching errors.

    Returns True on success, False on failure.
    """
    logger.info("=" * 60)
    logger.info("STEP: %s", name)
    logger.info("=" * 60)
    start = time.time()
    try:
        result = func(**kwargs)
        elapsed = time.time() - start
        if isinstance(result, dict):
            logger.info(
                "STEP %s completed in %.1fs — %d records",
                name, elapsed, len(result),
            )
        else:
            logger.info("STEP %s completed in %.1fs", name, elapsed)
        return True
    except Exception:
        elapsed = time.time() - start
        logger.error(
            "STEP %s FAILED after %.1fs:\n%s",
            name, elapsed, traceback.format_exc(),
        )
        return False


def run_pipeline(
    skip_fetch: bool = False,
    state_filter: str | None = None,
    skip_census: bool = False,
    skip_bea: bool = False,
    skip_fred: bool = False,
    skip_treasury: bool = False,
    skip_itep: bool = False,
    skip_taxfoundation: bool = False,
    skip_irs_migration: bool = False,
    skip_lincoln: bool = False,
    skip_pages: bool = False,
) -> dict:
    """
    Run the full data pipeline.

    Parameters
    ----------
    skip_fetch : bool
        If True, skip all fetch steps and only rebuild profiles.
    state_filter : str or None
        If set, only build the profile for this state abbreviation.
    skip_census, skip_bea, skip_fred, skip_treasury : bool
        Skip individual fetch steps.
    skip_itep, skip_taxfoundation : bool
        Skip ITEP or Tax Foundation processing steps.
    skip_irs_migration : bool
        Skip IRS SOI migration data fetch.
    skip_lincoln : bool
        Skip Lincoln Institute property tax processing.
    skip_pages : bool
        Skip state page markdown generation.

    Returns
    -------
    dict
        Summary of step results (step_name -> success bool).
    """
    ensure_dirs()
    results = {}
    total_start = time.time()

    logger.info("Pipeline started")
    logger.info("Options: skip_fetch=%s, state=%s", skip_fetch, state_filter or "ALL")

    if not skip_fetch:
        # Step 1: Census tax collections
        if not skip_census:
            from scripts.fetch_census_tax import fetch_census_tax
            results["census_tax"] = _run_step("Census Tax Collections", fetch_census_tax)
        else:
            logger.info("Skipping Census tax fetch")

        # Step 2: BEA regional data
        if not skip_bea:
            from scripts.fetch_bea_regional import fetch_bea_regional
            results["bea_regional"] = _run_step("BEA Regional Data", fetch_bea_regional)
        else:
            logger.info("Skipping BEA regional fetch")

        # Step 3: FRED series
        if not skip_fred:
            from scripts.fetch_fred_series import fetch_fred_series
            results["fred_series"] = _run_step("FRED Economic Series", fetch_fred_series)
        else:
            logger.info("Skipping FRED series fetch")

        # Step 4: Treasury fiscal data
        if not skip_treasury:
            from scripts.fetch_treasury_fiscal import fetch_treasury_fiscal
            results["treasury_fiscal"] = _run_step(
                "Treasury Federal Transfers", fetch_treasury_fiscal
            )
        else:
            logger.info("Skipping Treasury fiscal fetch")
        # Step 4b: IRS SOI Migration data
        if not skip_irs_migration:
            from scripts.fetch_irs_soi_migration import fetch_irs_soi_migration
            results["irs_migration"] = _run_step(
                "IRS SOI Migration Data", fetch_irs_soi_migration
            )
        else:
            logger.info("Skipping IRS SOI migration fetch")
    else:
        logger.info("Skipping all fetch steps (--skip-fetch)")

    # Step 5: ITEP Who Pays processing
    if not skip_itep:
        from scripts.process_itep_whopays import process_itep_whopays
        results["itep_whopays"] = _run_step("ITEP Who Pays Processing", process_itep_whopays)
    else:
        logger.info("Skipping ITEP Who Pays processing")

    # Step 6: Tax Foundation Index processing
    if not skip_taxfoundation:
        from scripts.process_tax_foundation import process_tax_foundation
        results["tax_foundation"] = _run_step(
            "Tax Foundation Index Processing", process_tax_foundation
        )
    else:
        logger.info("Skipping Tax Foundation processing")

    # Step 6b: Lincoln Institute property tax processing
    if not skip_lincoln:
        from scripts.process_lincoln_property import process_lincoln_property
        results["lincoln_property"] = _run_step(
            "Lincoln Property Tax Processing", process_lincoln_property
        )
    else:
        logger.info("Skipping Lincoln property tax processing")

    # Step 7: Build state profiles
    from scripts.build_state_profiles import build_all_profiles
    results["build_profiles"] = _run_step(
        "Build State Profiles",
        build_all_profiles,
        state_filter=state_filter,
    )

    # Step 8: Generate state pages
    if not skip_pages:
        from scripts.generate_state_pages import generate_all_pages
        results["generate_pages"] = _run_step(
            "Generate State Pages",
            generate_all_pages,
            state_filter=state_filter,
        )
    else:
        logger.info("Skipping state page generation")

    # Summary
    total_elapsed = time.time() - total_start
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY (%.1fs total)", total_elapsed)
    logger.info("=" * 60)

    successes = sum(1 for v in results.values() if v)
    failures = sum(1 for v in results.values() if not v)
    for step, ok in results.items():
        status = "OK" if ok else "FAILED"
        logger.info("  %-30s %s", step, status)

    logger.info("Results: %d succeeded, %d failed", successes, failures)

    if failures:
        logger.warning(
            "Some pipeline steps failed. Check logs above for details. "
            "The pipeline continues past failures to produce partial results."
        )

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Tax Structure Research Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.run_pipeline                      # full pipeline (all steps)
  python -m scripts.run_pipeline --skip-fetch         # rebuild profiles + pages from existing data
  python -m scripts.run_pipeline --state CA           # single state only
  python -m scripts.run_pipeline --skip-pages         # skip markdown page generation
  python -m scripts.run_pipeline --skip-irs-migration # skip IRS SOI download
  python -m scripts.run_pipeline --skip-fetch --skip-pages  # just rebuild profile JSON
        """,
    )
    parser.add_argument(
        "--state", type=str, default=None,
        help="Process a single state only (two-letter abbreviation, e.g. CA)",
    )
    parser.add_argument(
        "--skip-fetch", action="store_true",
        help="Skip all data fetching; only rebuild profiles from existing data",
    )
    parser.add_argument(
        "--skip-census", action="store_true",
        help="Skip the Census tax collections fetch",
    )
    parser.add_argument(
        "--skip-bea", action="store_true",
        help="Skip the BEA regional data fetch",
    )
    parser.add_argument(
        "--skip-fred", action="store_true",
        help="Skip the FRED economic series fetch",
    )
    parser.add_argument(
        "--skip-treasury", action="store_true",
        help="Skip the Treasury fiscal data fetch",
    )
    parser.add_argument(
        "--skip-itep", action="store_true",
        help="Skip the ITEP Who Pays processing step",
    )
    parser.add_argument(
        "--skip-taxfoundation", action="store_true",
        help="Skip the Tax Foundation Index processing step",
    )
    parser.add_argument(
        "--skip-irs-migration", action="store_true",
        help="Skip the IRS SOI migration data fetch",
    )
    parser.add_argument(
        "--skip-lincoln", action="store_true",
        help="Skip the Lincoln Institute property tax processing",
    )
    parser.add_argument(
        "--skip-pages", action="store_true",
        help="Skip state page markdown generation",
    )

    args = parser.parse_args()

    results = run_pipeline(
        skip_fetch=args.skip_fetch,
        state_filter=args.state,
        skip_census=args.skip_census,
        skip_bea=args.skip_bea,
        skip_fred=args.skip_fred,
        skip_treasury=args.skip_treasury,
        skip_itep=args.skip_itep,
        skip_taxfoundation=args.skip_taxfoundation,
        skip_irs_migration=args.skip_irs_migration,
        skip_lincoln=args.skip_lincoln,
        skip_pages=args.skip_pages,
    )

    # Exit with non-zero status if any step failed
    if any(not v for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
