# HELIOS ETF FLOW

Sector-level capital allocation diagnostic layer.

Measures where capital is being allocated across 11 sector ETFs relative to the broad market (SPY).

**This is NOT a signal, NOT a timing tool, NOT a trend indicator.**
OVERWEIGHT means "capital is flowing IN", not "buy". UNDERWEIGHT means "capital is flowing OUT", not "sell".

## Architecture

```
Unusual Whales (/api/etfs/{t}/in-outflow)  → AP: ETF fund flow (change_prem)
  fallback: Polygon DollarFlow proxy       → AP: Volume × (Close − Open)
Polygon.io (ETF + SPY daily OHLCV)         → RS: Excess Return vs SPY
  → Z-score normalization (63-day rolling, NO clipping)
  → CAS = 0.6 × z_AP + 0.4 × z_RS             [per sector]
  → State classification (5 states, threshold-based)
  → Explanation generation
  → Dashboard (Streamlit) / Parquet persistence
```

### Composite Allocation Score (CAS)

| Component | Weight | Source | Description |
|-----------|--------|--------|-------------|
| AP (Allocation Pressure) | 0.60 | Unusual Whales ETF fund flow (Polygon proxy fallback) | Daily net creation/redemption flow per sector |
| RS (Relative Strength) | 0.40 | Polygon daily returns | `ETF return − SPY return` |

### Allocation States

| State | CAS Threshold | Description |
|-------|--------------|-------------|
| OVERWEIGHT | > +1.0σ | Strong positive allocation pressure |
| ACCUMULATING | +0.3 to +1.0 | Building allocation pressure |
| NEUTRAL | −0.3 to +0.3 | Balanced allocation |
| DECREASING | −1.0 to −0.3 | Declining allocation pressure |
| UNDERWEIGHT | < −1.0σ | Strong negative allocation pressure |

### Universe (Fixed)

| Ticker | Sector |
|--------|--------|
| XLY | Consumer Discretionary |
| XLI | Industrials |
| XLF | Financials |
| XLE | Energy |
| XLK | Technology |
| XLP | Consumer Staples |
| XLV | Health Care |
| XLU | Utilities |
| XLB | Materials |
| XLRE | Real Estate |
| AGG | Aggregate Bond |

Benchmark: **SPY** (S&P 500)

## Setup

```bash
# Install dependencies
uv sync
uv sync --extra dev    # Include dev dependencies

# Configure API keys
cp .env.example .env
# Edit .env with your API keys (POLYGON_KEY required, UW_API_KEY recommended)
```

### Required API Keys

| Provider | Variable | Required | Notes |
|----------|----------|----------|-------|
| Polygon.io | `POLYGON_KEY` | Yes | Free tier (5 RPM) sufficient |
| Unusual Whales | `UW_API_KEY` | Recommended | ETF fund flow data for AP; falls back to Polygon proxy if missing |
| FMP | `FMP_KEY` | No | Not used by daily pipeline |

## Usage

```bash
# Run daily calculation
uv run python scripts/run_daily.py
uv run python scripts/run_daily.py --date 2026-02-04
uv run python scripts/run_daily.py --force --verbose

# Check API health
uv run python scripts/diagnose_api.py

# Launch dashboard (port 8504)
uv run streamlit run helios/dashboard/app.py --server.port 8504
```

### Example Output

```
========================================================================
HELIOS ETF FLOW RESULT
========================================================================
Date:       2026-02-05
Status:     COMPLETE
------------------------------------------------------------------------
Sector Name                      CAS State          AP(z)   RS(z)
------------------------------------------------------------------------
XLY    Consumer Discretionary   -0.58 DECREASING    -1.12   +0.23
XLI    Industrials              +0.42 ACCUMULATING   +0.61   +0.13
XLK    Technology               -0.71 DECREASING    -0.85   -0.50
AGG    Aggregate Bond           +2.09 OVERWEIGHT    +1.82   +2.50
========================================================================
```

## Testing

```bash
uv run pytest                        # All tests (66 tests)
uv run pytest -m unit                # Unit tests only
uv run pytest -k "test_no_clipping"  # Specific tests
uv run ruff check helios/            # Lint
uv run mypy helios/                  # Type check
```

### Key Test Guardrails

- `test_no_clipping_positive` / `test_no_clipping_negative` — z-scores beyond ±3 are preserved
- `test_per_sector_independence` — sector rolling windows are fully isolated
- Boundary tests for all 5 state thresholds (CAS = ±1.0, ±0.3)

## Project Structure

```
helios_etf/
├── helios/
│   ├── core/           # Types, constants, config, exceptions
│   ├── ingest/         # Polygon + Unusual Whales API clients, cache, rate limiter
│   ├── features/       # AP + RS calculation, feature aggregator
│   ├── normalization/  # Rolling z-scores (63d window, 21 min obs)
│   ├── scoring/        # CAS composite, state classifier, engine
│   ├── explain/        # Natural language explanation generator
│   ├── pipeline/       # Daily orchestrator (history backfill)
│   └── dashboard/      # Streamlit app (heatmap, cards, charts)
├── scripts/            # CLI entry points
├── tests/              # 66 unit tests
├── config/             # YAML configuration
└── data/               # Runtime: API cache + history parquet
```

## Data Persistence

- **API cache**: `data/raw/polygon/` (JSON, 7-day TTL), `data/raw/unusual_whales/` (JSON, 1-day TTL)
- **History**: `data/processed/helios/helios_history.parquet` (rows per date × ticker)
- **Daily snapshot**: `data/processed/helios/{date}.parquet`

The pipeline processes ~80 historical trading days on each run to build rolling baselines. The first 21 days produce `INSUFFICIENT` status (below minimum observations).

## Design Decisions

1. **NO z-score clipping** — tail information is preserved
2. **Weights are FROZEN** — `AP: 0.6, RS: 0.4` are conceptual, not optimized
3. **Thresholds are FROZEN** — direct z-score space, no percentile ranking
4. **Universe is FROZEN** — 11 ETFs, not dynamically constructed
5. **Per-sector independence** — 22 independent rolling windows (11 tickers × 2 features)
6. **UW fund flow with Polygon fallback** — AP prefers Unusual Whales ETF creation/redemption data, falls back to Polygon dollar volume proxy
7. **Sequential history processing** — all historical days processed to build baselines
