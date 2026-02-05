"""
Daily HELIOS ETF FLOW calculation script.

Usage:
    uv run python scripts/run_daily.py
    uv run python scripts/run_daily.py --date 2026-02-04
    uv run python scripts/run_daily.py --force --verbose
"""

import argparse
import asyncio
import logging
import sys
from datetime import date

from helios.core.constants import SECTOR_NAMES
from helios.pipeline.daily import DailyPipeline


def main() -> None:
    """Run daily HELIOS calculation."""
    parser = argparse.ArgumentParser(description="HELIOS ETF FLOW Daily Calculation")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Trade date (YYYY-MM-DD). Default: today",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force data refresh even if cached",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Parse date
    trade_date = date.fromisoformat(args.date) if args.date else None

    # Run pipeline
    pipeline = DailyPipeline()
    result = asyncio.run(pipeline.run(trade_date, args.force))

    # Print results
    print()
    print("=" * 72)
    print("HELIOS ETF FLOW RESULT")
    print("=" * 72)
    print(f"Date:       {result.trade_date}")
    print(f"Status:     {result.status.value}")
    print("-" * 72)
    print(f"{'Sector':<6} {'Name':<25} {'CAS':>7} {'State':<14} {'AP(z)':>7} {'RS(z)':>7}")
    print("-" * 72)

    for sector in result.sectors:
        name = SECTOR_NAMES.get(sector.ticker, sector.ticker)
        print(
            f"{sector.ticker:<6} {name:<25} "
            f"{sector.allocation_score:+7.2f} {sector.state.value:<14} "
            f"{sector.ap_zscore:+7.2f} {sector.rs_zscore:+7.2f}"
        )

    print("=" * 72)

    # Print state distribution
    from collections import Counter

    state_counts = Counter(s.state.value for s in result.sectors)
    print("\nState Distribution:")
    for state, count in sorted(state_counts.items()):
        print(f"  {state:<14} {count}")

    # Print JSON output
    print("\nJSON Output:")
    import json

    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
