# TradingAgents-jpn Product Requirements Document

## 1. Product Summary

TradingAgents-jpn is a Japan-oriented equity research copilot for internal investment committees, advisory teams, and research support workflows.

The product is not an auto-trading system. It generates structured Japanese research recommendations, preserves reasoning for audit, and keeps the boundary clear that the output is research support only.

Primary product label:

`JP Equity Research Copilot`

External Japanese labels:

- `日本株 AI リサーチ補助ツール`
- `日本株 投資委員会 Copilot`

One-line pitch:

`複数の専門エージェントが、株価・財務・ニュース・市場心理・リスクを分担分析し、投資委員会形式の日本語レポートを自動生成します。`

## 2. Target Users

- Japanese small-to-mid-sized asset managers
- Internal investment committees
- Financial advisory and research support teams
- Fintech products that need a Japan-market research layer before any execution tooling

## 3. Product Principles

- Default to Japan equity research rather than a generic trading demo.
- Produce research recommendations, not automatic trade execution.
- Make risk, opposing views, and next checkpoints first-class outputs.
- Prefer Japanese business and investment-committee language over plain `BUY / SELL signal` wording.
- Preserve enough input, configuration, model, data-source, and rationale metadata for internal review.
- Avoid implying live Japanese local-market coverage until the relevant connector is actually implemented.

## 4. Default Market Profile

The default repository profile is `jp_equity`.

Required default behavior:

- Output language defaults to `Japanese`.
- Bare four-digit Japanese equity tickers are normalized to Tokyo suffix form, for example `7203 -> 7203.T`.
- Tokyo-listed equities default to benchmark `^N225`.
- Runtime benchmark override supports alternatives such as `^TOPX`.
- Date, currency, company, and financial terminology should be presented in a Japan-business style where the report is user-facing.
- Non-JP/global profile must remain possible without forcing Japanese committee fields into every final output.

## 5. Report Requirements

In `jp_equity` mode, the final recommendation must use an investment-committee style report shape.

Required final recommendation fields:

- `投資判断`: exactly one of `買い / 中立 / 売り`
- `確信度`
- `主要根拠`
- `反対意見`
- `最大リスク`
- `次に確認すべき材料`

The report may also include global framework fields such as rating, executive summary, investment thesis, price target, and time horizon.

For non-JP/global mode, the core portfolio decision should still work without requiring the Japanese committee fields.

## 6. Risk And Compliance Requirements

The product must clearly state:

`投資助言ではありません`

Required boundaries:

- Default execution mode is `research_only`.
- The system does not directly execute real trades.
- Outputs are research recommendations for internal review, not investment advice.
- Trading or order-execution integrations are out of scope for the default product profile.

## 7. Audit Requirements

Each completed analysis should preserve an audit trail suitable for internal review.

Required audit metadata:

- timestamp
- ticker
- analysis date
- market profile
- asset type
- output language
- benchmark
- execution mode
- disclaimer
- LLM provider and model IDs
- configured data vendors
- Japan data-source configuration
- final signal
- final trade decision text
- investment plan
- path to the full state log

In `jp_equity` mode, the audit trail should also preserve:

- `投資判断`
- `確信度`
- `主要根拠`
- `反対意見`
- `最大リスク`
- `次に確認すべき材料`

Structured Portfolio Manager output should be used as the preferred source for audit fields. Markdown parsing is a fallback for free-text provider paths.

Audit log failure should not destroy the completed report/state output. It should be logged as a warning while preserving the main artifacts.

## 8. Japan Data Layer Requirements

The product should expose Japan-specific data extension points without overclaiming live coverage.

Target data directions:

- Japanese macro context
- BOJ policy
- `USD/JPY`
- `JGB` yields
- `TOPIX / Nikkei` comparison
- `TDnet`
- `EDINET`
- `有価証券報告書`
- `決算短信` summaries
- Tokyo Stock Exchange sector classification

Current implemented status:

- `jp_placeholder` provider exposes deterministic placeholder adapters with `source_label` and `fetched_at_utc`.
- `phase4_yfinance_mock` provider exposes a routed offline Yahoo-Finance-style mock bundle for five Japanese equities.
- The mock provider is for validation only and must not be described as live market data.
- Live `TDnet`, `EDINET`, `BOJ`, `USD/JPY`, `JGB`, and `決算短信` connectors are not yet production feeds.

Phase 4 mock universe:

- `7203.T` Toyota Motor
- `6758.T` Sony Group
- `9984.T` SoftBank Group
- `8306.T` Mitsubishi UFJ Financial Group
- `7974.T` Nintendo

## 9. Key User Flows

### CLI JP Default Flow

Input:

- ticker: `7203`
- date: valid analysis date
- default profile: `jp_equity`

Expected:

- ticker is normalized to `7203.T`
- report language defaults to Japanese
- benchmark resolves to `^N225` unless explicitly overridden
- disclaimer is visible
- final recommendation includes the required committee fields
- report, full state log, memory log, and JSONL audit record are produced

### Benchmark Override Flow

Input:

- ticker: `7203.T`
- config or environment override: `benchmark_ticker = ^TOPX`

Expected:

- exported report header shows `^TOPX`
- JSONL audit record also shows `^TOPX`
- report and audit agree on benchmark

### Phase 4 Mock Validation Flow

Input:

- `data_vendors.japan_market_data = phase4_yfinance_mock`
- ticker: `7203.T`

Expected:

- JP tools route to the offline mock provider
- outputs include `source_label` and `fetched_at_utc`
- generated report and audit trail preserve mock provenance
- documentation clearly distinguishes this from live Japanese local-market feeds

## 10. Non-Goals

- Automatic real-trade execution
- Legal or regulated investment advice
- Production-grade Japanese disclosure ingestion before live connectors are implemented
- Claiming that mock Yahoo-style fixtures are authoritative market data
- Replacing human investment committee review

## 11. Acceptance Criteria

- Default config supports `jp_equity`, Japanese output, `.T` suffix completion, `^N225`, `research_only`, and audit logging.
- Portfolio Manager only requires Japanese committee fields in Japan equity mode.
- Report export uses the actual runtime benchmark and runtime profile/disclaimer.
- Audit records prefer structured PM payloads and preserve multi-line rationale.
- Phase 4 mock data is available through a real routed provider, not only a fixture file.
- README and one-pager derive their product claims from this PRD and do not introduce conflicting status claims.
- E2E checklist distinguishes framework completeness from runtime validation.

## 12. Current Validation Status

Static implementation and syntax checks have been performed for the current code path.

Runtime validation still depends on running the test suite and/or the E2E checklist in an environment with required dependencies installed.
