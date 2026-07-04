"""Placeholder Japan-market data adapters.

These helpers intentionally avoid live network calls. They provide a stable
interface and an explicit status message so the rest of the framework can
reference planned Japanese data sources without fabricating coverage.
"""

from __future__ import annotations

from datetime import datetime, timezone

from tradingagents.dataflows.config import get_config


def _source_status_block() -> str:
    sources = get_config().get("japan_data_sources", {})
    lines = []
    for key in (
        "nikkei",
        "tdnet",
        "edinet",
        "boj",
        "fx_usd_jpy",
        "jgb_yields",
        "topix_sector",
        "earnings_digest",
    ):
        meta = sources.get(key, {})
        status = meta.get("status", "unknown")
        enabled = "enabled" if meta.get("enabled") else "disabled"
        lines.append(f"- {key}: {enabled} ({status})")
    return "\n".join(lines)


def _fetched_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_japan_market_context(curr_date: str) -> str:
    """Return a deterministic snapshot of configured JP-market data coverage."""
    return "\n".join([
        "JAPAN_MARKET_CONTEXT",
        f"- current_date: {curr_date}",
        f"- fetched_at_utc: {_fetched_at()}",
        "- mode: placeholder_adapter",
        "- source_label: jp_placeholder.market_context",
        "- note: Live Japanese market connectors are not active in this environment.",
        "- planned_sources:",
        _source_status_block(),
        "- suggested_signals: BOJ policy stance, USD/JPY trend, JGB yields, TOPIX/Nikkei relative performance.",
    ])


def get_japan_macro_indicators(curr_date: str) -> str:
    """Return a deterministic placeholder for BOJ, FX, and JGB macro coverage."""
    return "\n".join([
        "JAPAN_MACRO_INDICATORS",
        f"- current_date: {curr_date}",
        f"- fetched_at_utc: {_fetched_at()}",
        "- source_label: jp_placeholder.macro_indicators",
        "- note: Placeholder interface for BOJ policy, USD/JPY, and JGB data.",
        "- planned_feeds:",
        "- boj_policy: pending_connector",
        "- usd_jpy: pending_connector",
        "- jgb_yields: pending_connector",
        "- topix_nikkei_relative: pending_connector",
        "- analyst_instruction: Cite this block as planned local coverage when no live connector is enabled.",
    ])


def get_japan_company_disclosures(ticker: str, curr_date: str) -> str:
    """Return a deterministic placeholder for JP disclosure coverage."""
    return "\n".join([
        "JAPAN_COMPANY_DISCLOSURES",
        f"- ticker: {ticker}",
        f"- current_date: {curr_date}",
        f"- fetched_at_utc: {_fetched_at()}",
        "- mode: placeholder_adapter",
        "- source_label: jp_placeholder.company_disclosures",
        "- note: TDnet / EDINET / earnings-digest connectors are defined as extension points but not yet live.",
        "- planned_sources:",
        _source_status_block(),
        "- usage_guidance: If no disclosure connector is enabled, explicitly report the gap instead of inferring filing details.",
    ])


def get_japan_earnings_digest(ticker: str, curr_date: str) -> str:
    """Return a deterministic placeholder for JP earnings-summary coverage."""
    return "\n".join([
        "JAPAN_EARNINGS_DIGEST",
        f"- ticker: {ticker}",
        f"- current_date: {curr_date}",
        f"- fetched_at_utc: {_fetched_at()}",
        "- source_label: jp_placeholder.earnings_digest",
        "- note: Placeholder interface for 決算短信 summary extraction.",
        "- planned_fields: revenue, operating_profit, company_guidance, segment_commentary, shareholder_return_notes.",
        "- analyst_instruction: Distinguish clearly between live company disclosures and this placeholder digest interface.",
    ])
