# HELIOS ETF FLOW

Sector-level capital allocation diagnostic layer.
Describes WHERE capital is flowing across sector ETFs relative to the market.

**This is NOT a signal, NOT a timing tool, NOT a trend indicator.**

## Quick Commands

```bash
# Setup
uv sync                              # Install dependencies
uv sync --extra dev                  # Include dev dependencies

# Run
uv run python scripts/run_daily.py   # Daily calculation
uv run python scripts/diagnose_api.py # Check API health

# Test
uv run pytest                         # All tests
uv run pytest -m unit                # Unit tests only
uv run pytest -k "test_no_clipping"  # Specific test

# Lint & Type
uv run ruff check helios/            # Lint
uv run mypy helios/                  # Type check

# Dashboard
uv run streamlit run helios/dashboard/app.py --server.port 8504
```

## Required API Keys

| Provider   | Environment Variable |
|------------|---------------------|
| Polygon.io | POLYGON_KEY         |
| FMP        | FMP_KEY             |

## Data Flow

```
Polygon (ETF prices + SPY) + FMP (ETF net fund flows)
  -> Async Ingest (rate-limited, cached)
  -> Feature Extraction (AP: net flow, RS: excess return per sector)
  -> Z-score Normalization (63d rolling, NO clipping)
  -> CAS = 0.6*AP + 0.4*RS (per sector)
  -> State Classification (threshold-based)
  -> Explanation Generation
  -> Dashboard / Parquet persistence
```

## Critical Design Decisions (DO NOT CHANGE)

1. **NO Z-SCORE CLIPPING** at feature level — tail information is preserved
2. **Weights are FROZEN**: `{"AP": 0.6, "RS": 0.4}` — NOT optimized parameters
3. **State thresholds are FROZEN**: >+1.0 OVERWEIGHT, +0.3..+1.0 ACCUMULATING, -0.3..+0.3 NEUTRAL, -1.0..-0.3 DECREASING, <-1.0 UNDERWEIGHT
4. **Universe is FROZEN**: XLY, XLI, XLF, XLE, XLK, XLP, XLV, XLU, XLB, XLRE, AGG
5. **Rolling window**: 63 days, minimum 21 observations
6. **No alerts** — passive diagnostic only
7. **No intraday data** — daily ETF data only
8. **No combination with OBSIDIAN** internally
9. **No %Above MA** — that belongs to AURORA
10. OVERWEIGHT means "capital is flowing IN", NOT "buy"
11. UNDERWEIGHT means "capital is flowing OUT", NOT "sell"
