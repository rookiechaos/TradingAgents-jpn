from __future__ import annotations

import json

import pytest

from cli.main import resolve_report_benchmark, save_report_to_disk
from tradingagents.agents.schemas import PortfolioDecision, PortfolioRating, render_pm_decision
from tradingagents.agents.utils.agent_utils import extract_markdown_section
from tradingagents.dataflows.config import get_config, set_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.yfinance_news import get_global_news_yfinance


def _make_graph_stub():
    trading_graph = pytest.importorskip("tradingagents.graph.trading_graph")
    graph = object.__new__(trading_graph.TradingAgentsGraph)
    return graph


@pytest.mark.unit
def test_render_pm_decision_contains_required_japanese_committee_fields():
    decision = PortfolioDecision(
        rating=PortfolioRating.BUY,
        executive_summary="Build a starter position on weakness.",
        investment_thesis="Order momentum and capital discipline support upside.",
        investment_judgment="買い",
        confidence="高",
        key_reasons="受注の改善と利益率の安定。",
        counterarguments="外需減速なら前提が崩れる。",
        biggest_risk="ガイダンス下方修正。",
        next_checkpoints="次回決算、受注残、為替感応度。",
    )

    rendered = render_pm_decision(decision)
    assert "**投資判断**: 買い" in rendered
    assert "**確信度**: 高" in rendered
    assert "**主要根拠**: 受注の改善と利益率の安定。" in rendered
    assert "**反対意見**: 外需減速なら前提が崩れる。" in rendered
    assert "**最大リスク**: ガイダンス下方修正。" in rendered
    assert "**次に確認すべき材料**: 次回決算、受注残、為替感応度。" in rendered


@pytest.mark.unit
def test_japan_market_context_route_returns_placeholder_extension_point():
    result = route_to_vendor("get_japan_market_context", "2026-06-25")
    assert "JAPAN_MARKET_CONTEXT" in result
    assert "planned_sources" in result
    assert "source_label: jp_placeholder.market_context" in result


@pytest.mark.unit
def test_japan_macro_and_earnings_routes_return_source_labels():
    macro = route_to_vendor("get_japan_macro_indicators", "2026-06-25")
    earnings = route_to_vendor("get_japan_earnings_digest", "7203.T", "2026-06-25")
    assert "JAPAN_MACRO_INDICATORS" in macro
    assert "source_label: jp_placeholder.macro_indicators" in macro
    assert "JAPAN_EARNINGS_DIGEST" in earnings
    assert "source_label: jp_placeholder.earnings_digest" in earnings


@pytest.mark.unit
def test_japan_market_routes_can_use_phase4_yfinance_mock_provider():
    before = get_config()
    try:
        set_config({"data_vendors": {"japan_market_data": "phase4_yfinance_mock"}})
        context = route_to_vendor("get_japan_market_context", "2026-06-25")
        disclosures = route_to_vendor("get_japan_company_disclosures", "7203.T", "2026-06-25")
        earnings = route_to_vendor("get_japan_earnings_digest", "7203.T", "2026-06-25")

        assert "source_label: phase4_yfinance_mock.market_context" in context
        assert "7203.T (Toyota Motor Corporation)" in context
        assert "source_label: phase4_yfinance_mock.company_disclosures" in disclosures
        assert "Toyota Motor Corporation" in disclosures
        assert "source_label: phase4_yfinance_mock.earnings_digest" in earnings
        assert "- latest_close_jpy: 3430.0" in earnings
    finally:
        set_config(before)


@pytest.mark.unit
def test_audit_log_appends_jsonl_record(tmp_path):
    graph = _make_graph_stub()
    graph.config = {
        "audit_log_path": str(tmp_path / "audit.jsonl"),
        "market_profile": "jp_equity",
        "output_language": "Japanese",
        "trade_execution_mode": "research_only",
        "research_only_notice": "投資助言ではありません。",
        "llm_provider": "openai",
        "deep_think_llm": "gpt-5.5",
        "quick_think_llm": "gpt-5.4-mini",
        "data_vendors": {"news_data": "yfinance"},
        "japan_data_sources": {"tdnet": {"enabled": False, "status": "planned"}},
        "benchmark_map": {".T": "^N225", "": "SPY"},
        "benchmark_ticker": None,
    }
    graph.process_signal = lambda text: "Buy"

    final_state = {
        "company_of_interest": "7203.T",
        "asset_type": "stock",
        "final_trade_decision": (
            "**Rating**: Buy\n\n"
            "**投資判断**: 買い\n\n"
            "**確信度**: 高\n\n"
            "**主要根拠**: 受注改善と自社株買い。\n\n"
            "**反対意見**: 外需減速リスク。\n\n"
            "**最大リスク**: ガイダンス下振れ。\n\n"
            "**次に確認すべき材料**: 次回決算。"
        ),
        "investment_plan": "Research plan",
    }
    log_path = tmp_path / "full_states_log_2026-06-25.json"
    log_path.write_text("{}", encoding="utf-8")

    graph._append_audit_log("2026-06-25", final_state, log_path)

    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["ticker"] == "7203.T"
    assert record["benchmark"] == "^N225"
    assert record["execution_mode"] == "research_only"
    assert record["final_signal"] == "Buy"
    assert record["main_reasons"] == "受注改善と自社株買い。"
    assert record["biggest_risk"] == "ガイダンス下振れ。"


@pytest.mark.unit
def test_extract_markdown_section_keeps_multiline_body():
    text = (
        "**主要根拠**: 受注改善。\n"
        "- 自社株買いの継続\n"
        "- 円安メリット\n\n"
        "**反対意見**: バリュエーション負担。"
    )
    assert extract_markdown_section(text, "主要根拠") == (
        "受注改善。\n- 自社株買いの継続\n- 円安メリット"
    )


@pytest.mark.unit
def test_extract_markdown_section_supports_heading_fallback_shape():
    text = (
        "### 主要根拠\n"
        "受注改善。\n"
        "- 自社株買いの継続\n\n"
        "### 反対意見\n"
        "バリュエーション負担。"
    )
    assert extract_markdown_section(text, "主要根拠") == "受注改善。\n- 自社株買いの継続"


@pytest.mark.unit
def test_audit_log_preserves_multiline_committee_sections(tmp_path):
    graph = _make_graph_stub()
    graph.config = {
        "audit_log_path": str(tmp_path / "audit.jsonl"),
        "market_profile": "jp_equity",
        "output_language": "Japanese",
        "trade_execution_mode": "research_only",
        "research_only_notice": "投資助言ではありません。",
        "llm_provider": "openai",
        "deep_think_llm": "gpt-5.5",
        "quick_think_llm": "gpt-5.4-mini",
        "data_vendors": {"news_data": "yfinance"},
        "japan_data_sources": {"tdnet": {"enabled": False, "status": "planned"}},
        "benchmark_map": {".T": "^N225", "": "SPY"},
        "benchmark_ticker": None,
    }
    graph.process_signal = lambda text: "Buy"

    final_state = {
        "company_of_interest": "7203.T",
        "asset_type": "stock",
        "final_trade_decision": (
            "**Rating**: Buy\n\n"
            "**投資判断**: 買い\n\n"
            "**確信度**: 高\n\n"
            "**主要根拠**: 受注改善。\n"
            "- 自社株買いの継続\n"
            "- 円安メリット\n\n"
            "**反対意見**: バリュエーション負担。\n"
            "- 短期では織り込み済みの懸念\n\n"
            "**最大リスク**: ガイダンス下振れ。\n\n"
            "**次に確認すべき材料**: 次回決算。"
        ),
        "investment_plan": "Research plan",
    }
    log_path = tmp_path / "full_states_log_2026-06-25.json"
    log_path.write_text("{}", encoding="utf-8")

    graph._append_audit_log("2026-06-25", final_state, log_path)

    record = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["main_reasons"] == "受注改善。\n- 自社株買いの継続\n- 円安メリット"
    assert record["counterarguments"] == "バリュエーション負担。\n- 短期では織り込み済みの懸念"


@pytest.mark.unit
def test_audit_log_prefers_structured_committee_payload_when_available(tmp_path):
    graph = _make_graph_stub()
    graph.config = {
        "audit_log_path": str(tmp_path / "audit.jsonl"),
        "market_profile": "jp_equity",
        "output_language": "Japanese",
        "trade_execution_mode": "research_only",
        "research_only_notice": "投資助言ではありません。",
        "llm_provider": "openai",
        "deep_think_llm": "gpt-5.5",
        "quick_think_llm": "gpt-5.4-mini",
        "data_vendors": {"news_data": "yfinance"},
        "japan_data_sources": {"tdnet": {"enabled": False, "status": "planned"}},
        "benchmark_map": {".T": "^N225", "": "SPY"},
        "benchmark_ticker": None,
    }
    graph.process_signal = lambda text: "Buy"

    final_state = {
        "company_of_interest": "7203.T",
        "asset_type": "stock",
        "final_trade_decision": "### 主要根拠\nfallback text",
        "final_trade_decision_structured": {
            "investment_judgment": "買い",
            "confidence": "高",
            "key_reasons": "structured reasons",
            "counterarguments": "structured counter",
            "biggest_risk": "structured risk",
            "next_checkpoints": "structured next",
        },
        "investment_plan": "Research plan",
    }
    log_path = tmp_path / "full_states_log_2026-06-25.json"
    log_path.write_text("{}", encoding="utf-8")

    graph._append_audit_log("2026-06-25", final_state, log_path)
    record = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["investment_judgment"] == "買い"
    assert record["main_reasons"] == "structured reasons"
    assert record["final_trade_decision_structured"]["next_checkpoints"] == "structured next"


@pytest.mark.unit
def test_resolve_report_benchmark_prefers_runtime_config_override():
    benchmark = resolve_report_benchmark(
        "7203.T",
        final_state={},
        config={
            "benchmark_ticker": "^TOPX",
            "benchmark_map": {".T": "^N225", "": "SPY"},
        },
    )
    assert benchmark == "^TOPX"


@pytest.mark.unit
def test_save_report_to_disk_uses_runtime_benchmark_in_header(tmp_path):
    final_state = {
        "trade_date": "2026-06-25",
        "benchmark_ticker": "^TOPX",
        "market_report": "Market",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "investment_debate_state": {},
        "trader_investment_plan": "",
        "risk_debate_state": {},
    }
    report_path = save_report_to_disk(
        final_state,
        "7203.T",
        tmp_path,
        config={
            "market_profile": "jp_equity",
            "benchmark_ticker": "^TOPX",
            "benchmark_map": {".T": "^N225", "": "SPY"},
        },
    )
    text = report_path.read_text(encoding="utf-8")
    assert "- ベンチマーク: ^TOPX" in text


@pytest.mark.unit
def test_save_report_to_disk_uses_runtime_header_profile_and_notice(tmp_path):
    final_state = {
        "trade_date": "2026-06-25",
        "market_report": "Market",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": "",
        "investment_debate_state": {},
        "trader_investment_plan": "",
        "risk_debate_state": {},
    }
    report_path = save_report_to_disk(
        final_state,
        "NVDA",
        tmp_path,
        config={
            "market_profile": "global",
            "research_only_notice": "Research only.",
            "benchmark_map": {"": "SPY"},
        },
    )
    text = report_path.read_text(encoding="utf-8")
    assert "# Trading Analysis Report: NVDA" in text
    assert "- Disclaimer: Research only." in text


@pytest.mark.unit
def test_jp_profile_uses_japan_global_news_queries():
    before = get_config()
    try:
        set_config({
            "market_profile": "jp_equity",
            "global_news_queries": ["fallback query"],
            "jp_global_news_queries": ["boj query", "usd jpy query"],
        })
        seen_queries = []

        class DummySearch:
            def __init__(self, query, news_count, enable_fuzzy_query):
                seen_queries.append(query)
                self.news = []

        import tradingagents.dataflows.yfinance_news as news_mod

        class DummyYFinance:
            Search = DummySearch

        original_loader = news_mod._load_yfinance
        original_retry = news_mod.yf_retry
        try:
            news_mod._load_yfinance = lambda: DummyYFinance
            news_mod.yf_retry = lambda fn: fn()
            get_global_news_yfinance("2026-06-25", look_back_days=1, limit=1)
        finally:
            news_mod._load_yfinance = original_loader
            news_mod.yf_retry = original_retry

        assert seen_queries == ["boj query", "usd jpy query"]
    finally:
        set_config(before)
