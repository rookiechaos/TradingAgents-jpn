# Phase 4 Yahoo Finance Mock Fixtures

## Purpose

These fixtures provide an offline mock bundle for the Phase 4 Japan-market layer.

They are not live `TDnet`, `EDINET`, `BOJ`, `USD/JPY`, or `JGB` connectors. Instead, they use a Yahoo-Finance-style data shape as a first-stage stand-in so prompt, schema, audit, and report behavior can be validated without relying on external feeds.

## Coverage

The bundle currently includes 5 Japanese equities:

- `7203.T` Toyota Motor
- `6758.T` Sony Group
- `9984.T` SoftBank Group
- `8306.T` Mitsubishi UFJ Financial Group
- `7974.T` Nintendo

## Included Fields

Each record contains:

- `ticker`
- `company_name`
- `exchange`
- `currency`
- `benchmark`
- `identity`
- `ohlcv_sample`
- `fundamentals`
- `news_items`
- `phase4_mock_note`

## Intended Use

- Offline validation of JP prompt flows
- Fixture-driven tests for report generation and audit extraction
- Mock input for early Phase 4 work before live local-market connectors are available
- Routed provider mode via `data_vendors.japan_market_data = phase4_yfinance_mock`

## Provenance

These fixtures are modeled on the repository's Yahoo Finance output shape. They are curated mock data for development and validation, not authoritative market data.
