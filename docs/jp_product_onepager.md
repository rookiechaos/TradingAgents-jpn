# TradingAgents-jpn One Pager

This one-pager is a sales-facing summary derived from [prd.md](prd.md). The PRD is the source of truth for product scope, current implementation status, and non-goals.

## Product Name

`TradingAgents-jpn`

Suggested external labels:

- `JP Equity Research Copilot`
- `日本株 AI リサーチ補助ツール`
- `日本株 投資委員会 Copilot`

## One-Line Pitch

複数の専門エージェントが、株価・財務・ニュース・市場心理・リスクを分担分析し、投資委員会形式の日本語レポートを自動生成します。

## What It Does

- Accepts Japanese equity tickers such as `7203.T`
- Produces a Japanese investment-committee report by default
- Separates market, news, sentiment, fundamentals, risk, and final recommendation into specialist roles
- Preserves an audit trail with ticker, date, model/provider, benchmark, and final reasoning
- Uses the actual runtime benchmark in exported reports, including explicit overrides such as `^TOPX`

## Report Shape

Every final recommendation is structured around:

- `投資判断`
- `確信度`
- `主要根拠`
- `反対意見`
- `最大リスク`
- `次に確認すべき材料`

## Why It Fits Japanese Customers

- The output reads like an internal investment-committee memo instead of a generic `BUY / SELL` bot signal
- Risk, opposing views, and next checkpoints are always explicit
- The default profile is aligned to Japanese equities, benchmarks, and language
- The product boundary is conservative and easier to explain internally

## Target Users

- Small and mid-sized Japanese asset managers
- Internal investment committees
- Advisory and research support teams
- Fintech products that need a Japan-market research layer before execution tooling

## Product Boundary

`投資助言ではありません`

- Research support only
- No automatic real-trade execution in the default profile
- Intended for internal review, idea generation, and explainable first-pass analysis

## Data Layer Direction

Per the PRD, current extension points are prepared for:

- BOJ policy
- `USD/JPY`
- `JGB` yields
- `TOPIX / Nikkei` comparison
- `TDnet`
- `EDINET`
- `決算短信` summaries

Current status:

- End-to-end workflow shape is implemented
- Provenance fields such as `source_label` and `fetched_at_utc` are preserved
- `phase4_yfinance_mock` is available as a routed offline validation provider for five Japanese equities
- `jp_placeholder` remains available for deterministic extension-point coverage
- Live Japan-specific feeds are not yet production connectors

## Demo Message

TradingAgents-jpn helps Japanese investment teams turn fragmented market, macro, and company information into a single structured research recommendation they can actually review, debate, and audit.
