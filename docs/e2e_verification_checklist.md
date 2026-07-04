# E2E Verification Checklist

## Scope

This checklist is for validation only and derives from [prd.md](prd.md). It is intentionally focused on confirming that the current code path behaves as designed, without adding new features during the verification pass.

## Preconditions

- Valid Python environment for the repo
- Required dependencies installed
- At least one LLM provider configured
- Optional:
  - `TRADINGAGENTS_BENCHMARK_TICKER=^TOPX` for benchmark-override verification
  - local writable results directory

## Entry Points To Run

### 1. CLI Default JP Flow

Entry:

```bash
python -m cli.main
```

Inputs:

- ticker: `7203`
- date: a valid past trading date
- output language: default
- provider: any configured provider

Expected:

- input `7203` is normalized to `7203.T`
- output language defaults to Japanese
- disclaimer `投資助言ではありません` is visible in the CLI
- final recommendation includes:
  - `投資判断`
  - `確信度`
  - `主要根拠`
  - `反対意見`
  - `最大リスク`
  - `次に確認すべき材料`

Artifacts:

- on-screen final report
- saved report directory under results
- JSON state log
- JSONL audit record

### 2. CLI Benchmark Override Flow

Entry:

```bash
TRADINGAGENTS_BENCHMARK_TICKER=^TOPX python -m cli.main
```

Inputs:

- ticker: `7203.T`
- date: a valid past trading date

Expected:

- run completes in JP profile
- exported report header shows `^TOPX`
- audit log benchmark field also shows `^TOPX`

Artifacts:

- `complete_report.md`
- JSONL audit record

### 3. Programmatic Graph Flow

Entry:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

cfg = DEFAULT_CONFIG.copy()
graph = TradingAgentsGraph(debug=False, config=cfg)
final_state, signal = graph.propagate("7203.T", "2026-06-25")
```

Expected:

- `final_state["final_trade_decision"]` contains the JP committee fields
- `signal` resolves to a canonical rating like `Buy` / `Hold` / `Sell`
- result logs and audit logs are written

Artifacts:

- `final_state`
- parsed `signal`
- state log JSON
- JSONL audit record

### 4. Phase 4 Mock-Only Validation

Entry:

- no live market feed required
- set `data_vendors.japan_market_data = phase4_yfinance_mock`
- consume the fixture set in:
  - [tests/fixtures/phase4_yfinance_mock/README.md](../tests/fixtures/phase4_yfinance_mock/README.md)
  - [tests/fixtures/phase4_yfinance_mock/jp_equities_yfinance_mock.json](../tests/fixtures/phase4_yfinance_mock/jp_equities_yfinance_mock.json)

Expected:

- fixture set contains 5 Japanese equities
- each record includes identity, benchmark, OHLCV sample, fundamentals summary, and Yahoo-Finance-style news items
- JP tools route to an explicit `phase4_yfinance_mock` provider instead of only placeholder adapters
- fixture provenance is explicit and separate from live Phase 4 connectors

Artifacts:

- reusable offline mock dataset for Phase 4 prompt and schema validation

## What To Inspect

### Report Output

- final header shows the actual benchmark used
- disclaimer is present
- investment committee sections are all present
- Japanese language output is coherent enough for internal review

### Audit Output

- ticker
- trade date
- benchmark
- provider/model
- `投資判断`
- `確信度`
- multi-line `主要根拠`
- `反対意見`
- `最大リスク`
- `次に確認すべき材料`

### Japan Data Layer Behavior

- Phase 4 tool calls can be represented with provenance
- placeholder adapters are clearly distinguished from live data connectors
- Yahoo Finance mock bundle can stand in for early workflow testing
- mocked graph/CLI validation can export report and audit artifacts from the routed mock provider

## Pass Criteria

- CLI path completes with JP defaults
- report header and audit log agree on benchmark
- committee fields survive from generation to export and audit log
- offline Phase 4 mock bundle is usable for fixture-driven validation

## Current Limitation

This checklist verifies end-to-end runtime behavior only when actually executed. The repository contains routed Phase 4 mock-provider coverage and mocked graph/CLI E2E tests, but runtime validation still requires running the relevant tests or entry points in an environment with dependencies installed.
