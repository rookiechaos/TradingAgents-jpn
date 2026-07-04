"""Offline Phase 4 Yahoo-Finance-style mock provider for JP-market tests.

This provider is intentionally explicit about being a development-only fixture
adapter. It turns the static JSON bundle under ``tests/fixtures`` into routed
tool outputs so the Japan-market workflow can be validated end to end without
pretending these records are live TDnet / EDINET / BOJ feeds.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from tradingagents.dataflows.symbol_utils import NoMarketDataError


def _fixture_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / "tests" / "fixtures" / "phase4_yfinance_mock" / "jp_equities_yfinance_mock.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        "Phase 4 Yahoo mock fixture not found. Expected "
        f"{candidate}"
    )


@lru_cache(maxsize=1)
def _load_bundle() -> dict:
    return json.loads(_fixture_path().read_text(encoding="utf-8"))


def _fetched_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _records() -> list[dict]:
    return list(_load_bundle().get("records", []))


def _record_by_ticker(ticker: str) -> dict:
    normalized = ticker.strip().upper()
    for record in _records():
        if str(record.get("ticker", "")).upper() == normalized:
            return record
    raise NoMarketDataError(
        ticker,
        canonical=normalized,
        detail="Ticker not present in the offline phase4_yfinance_mock fixture bundle.",
    )


def get_japan_market_context(curr_date: str) -> str:
    records = _records()
    tickers = ", ".join(
        f"{record['ticker']} ({record['company_name']})"
        for record in records
    )
    benchmarks = sorted({record.get("benchmark", "^N225") for record in records})
    return "\n".join(
        [
            "JAPAN_MARKET_CONTEXT",
            f"- current_date: {curr_date}",
            f"- fetched_at_utc: {_fetched_at()}",
            "- mode: offline_mock_provider",
            "- source_label: phase4_yfinance_mock.market_context",
            "- provenance: tests/fixtures/phase4_yfinance_mock/jp_equities_yfinance_mock.json",
            "- source_shape: yfinance-inspired offline fixture bundle",
            f"- fixture_universe_count: {len(records)}",
            f"- available_tickers: {tickers}",
            f"- benchmark_candidates: {', '.join(benchmarks)}",
            "- note: Offline Phase 4 validation bundle. Not a live Japanese local-market connector.",
        ]
    )


def get_japan_macro_indicators(curr_date: str) -> str:
    records = _records()
    latest_dates = sorted(
        {
            row["date"]
            for record in records
            for row in record.get("ohlcv_sample", [])
            if row.get("date")
        }
    )
    return "\n".join(
        [
            "JAPAN_MACRO_INDICATORS",
            f"- current_date: {curr_date}",
            f"- fetched_at_utc: {_fetched_at()}",
            "- source_label: phase4_yfinance_mock.macro_indicators",
            "- mode: offline_mock_provider",
            "- benchmark_reference: ^N225",
            "- market_currency: JPY",
            f"- fixture_price_dates: {', '.join(latest_dates[-3:])}",
            "- note: This macro block is a validation-only JP context wrapper around the offline Yahoo-style fixture bundle.",
            "- analyst_instruction: Treat FX, BOJ, JGB, and TOPIX commentary as mock workflow coverage, not live macro data.",
        ]
    )


def get_japan_company_disclosures(ticker: str, curr_date: str) -> str:
    record = _record_by_ticker(ticker)
    news_lines = [
        f"- {item['published_at']} | {item['publisher']} | {item['title']}"
        for item in record.get("news_items", [])
    ]
    return "\n".join(
        [
            "JAPAN_COMPANY_DISCLOSURES",
            f"- ticker: {record['ticker']}",
            f"- current_date: {curr_date}",
            f"- fetched_at_utc: {_fetched_at()}",
            "- source_label: phase4_yfinance_mock.company_disclosures",
            "- mode: offline_mock_provider",
            f"- company_name: {record['company_name']}",
            f"- exchange: {record['exchange']}",
            f"- currency: {record['currency']}",
            f"- benchmark: {record['benchmark']}",
            f"- phase4_mock_note: {record['phase4_mock_note']}",
            "- yahoo_style_headlines:",
            *news_lines,
            "- note: Stand-in disclosure context assembled from the offline Yahoo-style mock bundle.",
        ]
    )


def get_japan_earnings_digest(ticker: str, curr_date: str) -> str:
    record = _record_by_ticker(ticker)
    fundamentals = record.get("fundamentals", {})
    latest_bar = record.get("ohlcv_sample", [])[-1]
    return "\n".join(
        [
            "JAPAN_EARNINGS_DIGEST",
            f"- ticker: {record['ticker']}",
            f"- current_date: {curr_date}",
            f"- fetched_at_utc: {_fetched_at()}",
            "- source_label: phase4_yfinance_mock.earnings_digest",
            "- mode: offline_mock_provider",
            f"- company_name: {record['company_name']}",
            f"- latest_close_date: {latest_bar.get('date', 'n/a')}",
            f"- latest_close_jpy: {latest_bar.get('close', 'n/a')}",
            f"- market_cap_jpy: {fundamentals.get('marketCap', 'n/a')}",
            f"- trailing_pe: {fundamentals.get('trailingPE', 'n/a')}",
            f"- price_to_book: {fundamentals.get('priceToBook', 'n/a')}",
            f"- dividend_yield: {fundamentals.get('dividendYield', 'n/a')}",
            f"- total_revenue_jpy: {fundamentals.get('totalRevenue', 'n/a')}",
            f"- net_income_to_common_jpy: {fundamentals.get('netIncomeToCommon', 'n/a')}",
            f"- debt_to_equity: {fundamentals.get('debtToEquity', 'n/a')}",
            "- note: Validation-only earnings digest derived from the offline Yahoo-style fixture bundle.",
        ]
    )
