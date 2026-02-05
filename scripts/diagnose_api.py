"""
API diagnostics script for HELIOS ETF FLOW.

Checks connectivity and authentication for Polygon and FMP APIs.

Usage:
    uv run python scripts/diagnose_api.py
"""

import asyncio
import logging
import sys

from helios.core.config import get_settings
from helios.ingest.fmp import FMPFlowClient
from helios.ingest.polygon import PolygonETFClient


async def diagnose() -> bool:
    """Run API diagnostics."""
    settings = get_settings()
    all_ok = True

    print("=" * 50)
    print("HELIOS ETF FLOW - API Diagnostics")
    print("=" * 50)

    # Check Polygon
    print("\n[Polygon.io]")
    print(f"  API Key: {settings.polygon_key[:8]}...{settings.polygon_key[-4:]}")
    try:
        async with PolygonETFClient(settings=settings) as client:
            ok = await client.health_check()
            status = "OK" if ok else "FAIL"
            print(f"  Health Check: {status}")
            if not ok:
                all_ok = False
    except Exception as e:
        print(f"  Health Check: ERROR - {e}")
        all_ok = False

    # Check FMP
    print("\n[FMP]")
    print(f"  API Key: {settings.fmp_key[:8]}...{settings.fmp_key[-4:]}")
    try:
        async with FMPFlowClient(settings=settings) as client:
            ok = await client.health_check()
            status = "OK" if ok else "FAIL"
            print(f"  Health Check: {status}")
            if not ok:
                all_ok = False
    except Exception as e:
        print(f"  Health Check: ERROR - {e}")
        all_ok = False

    print("\n" + "=" * 50)
    overall = "ALL SYSTEMS OK" if all_ok else "ISSUES DETECTED"
    print(f"Result: {overall}")
    print("=" * 50)

    return all_ok


def main() -> None:
    """Entry point."""
    logging.basicConfig(level=logging.WARNING)
    ok = asyncio.run(diagnose())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
