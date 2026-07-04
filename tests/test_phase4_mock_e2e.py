from __future__ import annotations

import copy
import functools
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cli.main import save_report_to_disk
from cli.utils import normalize_ticker_symbol
from tradingagents.agents.utils.agent_utils import build_instrument_context
from tradingagents.agents.utils.memory import TradingMemoryLog
from tradingagents.dataflows.config import get_config, set_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.default_config import DEFAULT_CONFIG

_propagation_mod = pytest.importorskip("tradingagents.graph.propagation")
_trading_graph_mod = pytest.importorskip("tradingagents.graph.trading_graph")

Propagator = _propagation_mod.Propagator
TradingAgentsGraph = _trading_graph_mod.TradingAgentsGraph


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "phase4_yfinance_mock"
    / "jp_equities_yfinance_mock.json"
)


def _mock_identity_for(ticker: str) -> dict:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    for record in payload["records"]:
        if record["ticker"] == ticker:
            identity = record["identity"].copy()
            identity["company_name"] = record["company_name"]
            identity["exchange"] = record["exchange"]
            return identity
    raise AssertionError(f"Ticker {ticker} not found in fixture")


def _committee_decision(ticker: str, disclosures: str, earnings: str) -> str:
    return (
        "**Rating**: Buy\n\n"
        "**投資判断**: 買い\n\n"
        "**確信度**: 高\n\n"
        "**主要根拠**: Phase 4 mock bundle confirms Toyota as the target company.\n"
        f"- {ticker} keeps the .T suffix through the workflow\n"
        "- Offline JP tools expose source labels and benchmark-aware context\n"
        "- Earnings digest shows a latest close of 3430.0 JPY with moderate valuation\n\n"
        "**反対意見**: The data path is still a mock provider.\n"
        "- Local filings, BOJ, and JGB connectors are not live feeds in this validation run\n\n"
        "**最大リスク**: Reviewers could confuse fixture-backed Yahoo-style data with production local-market coverage.\n\n"
        "**次に確認すべき材料**: Switch the same tool route from phase4_yfinance_mock to live TDnet/EDINET adapters.\n"
        f"- preserve provenance from {disclosures.splitlines()[4]}\n"
        f"- preserve provenance from {earnings.splitlines()[4]}"
    )


@pytest.mark.unit
def test_phase4_mock_provider_supports_mocked_graph_and_cli_e2e(tmp_path):
    before = get_config()
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["results_dir"] = str(tmp_path / "results")
    config["data_cache_dir"] = str(tmp_path / "cache")
    config["memory_log_path"] = str(tmp_path / "memory" / "trading_memory.md")
    config["audit_log_path"] = str(tmp_path / "audit" / "analysis_audit.jsonl")
    config["data_vendors"]["japan_market_data"] = "phase4_yfinance_mock"
    Path(config["audit_log_path"]).parent.mkdir(parents=True, exist_ok=True)

    try:
        set_config(config)
        normalized = normalize_ticker_symbol("7203")
        assert normalized == "7203.T"

        mock_graph = MagicMock()
        mock_graph.memory_log = TradingMemoryLog(config)
        mock_graph.log_states_dict = {}
        mock_graph.debug = False
        mock_graph.config = config
        mock_graph.propagator = Propagator()
        mock_graph._checkpointer_ctx = None
        mock_graph.signal_processor.process_signal.return_value = "Buy"
        mock_graph.resolve_instrument_context.return_value = build_instrument_context(
            normalized,
            identity=_mock_identity_for(normalized),
        )

        def fake_invoke(init_state, **kwargs):
            ticker = init_state["company_of_interest"]
            trade_date = init_state["trade_date"]
            market_context = route_to_vendor("get_japan_market_context", trade_date)
            macro = route_to_vendor("get_japan_macro_indicators", trade_date)
            disclosures = route_to_vendor("get_japan_company_disclosures", ticker, trade_date)
            earnings = route_to_vendor("get_japan_earnings_digest", ticker, trade_date)
            final_trade_decision = _committee_decision(ticker, disclosures, earnings)
            investment_debate_state = {
                "bull_history": market_context,
                "bear_history": disclosures,
                "history": f"{market_context}\n\n{macro}\n\n{disclosures}\n\n{earnings}",
                "current_response": "",
                "judge_decision": "JP mock workflow consolidated for committee review.",
                "count": 1,
            }
            risk_debate_state = {
                "aggressive_history": market_context,
                "conservative_history": earnings,
                "neutral_history": macro,
                "history": f"{disclosures}\n\n{earnings}",
                "latest_speaker": "Judge",
                "current_aggressive_response": "",
                "current_conservative_response": "",
                "current_neutral_response": "",
                "judge_decision": final_trade_decision,
                "count": 1,
            }
            return {
                **init_state,
                "company_of_interest": ticker,
                "trade_date": trade_date,
                "market_report": f"{market_context}\n\n{macro}",
                "sentiment_report": "",
                "news_report": disclosures,
                "fundamentals_report": earnings,
                "investment_debate_state": investment_debate_state,
                "investment_plan": (
                    "Use the routed JP mock provider as research support only and "
                    "carry benchmark context into committee review."
                ),
                "trader_investment_plan": "Research-only starter position plan for internal review.",
                "risk_debate_state": risk_debate_state,
                "final_trade_decision": final_trade_decision,
            }

        mock_graph.graph.invoke.side_effect = fake_invoke
        mock_graph._resolve_pending_entries.return_value = None
        mock_graph._resolve_benchmark = functools.partial(
            TradingAgentsGraph._resolve_benchmark, mock_graph
        )
        mock_graph._append_audit_log = functools.partial(
            TradingAgentsGraph._append_audit_log, mock_graph
        )
        mock_graph._log_state = functools.partial(
            TradingAgentsGraph._log_state, mock_graph
        )
        mock_graph._run_graph = functools.partial(
            TradingAgentsGraph._run_graph, mock_graph
        )

        final_state, signal = TradingAgentsGraph.propagate(
            mock_graph, normalized, "2026-06-25"
        )

        assert signal == "Buy"
        assert final_state["company_of_interest"] == "7203.T"
        assert "source_label: phase4_yfinance_mock.market_context" in final_state["market_report"]
        assert "source_label: phase4_yfinance_mock.company_disclosures" in final_state["news_report"]
        assert "source_label: phase4_yfinance_mock.earnings_digest" in final_state["fundamentals_report"]

        report_path = save_report_to_disk(
            final_state,
            normalized,
            tmp_path / "exported_report",
            config=config,
        )
        report_text = report_path.read_text(encoding="utf-8")
        assert "# 日本株投資委員会レポート: 7203.T" in report_text
        assert "- ベンチマーク: ^N225" in report_text
        assert "**投資判断**: 買い" in report_text
        assert "Toyota Motor Corporation" in report_text
        assert "phase4_yfinance_mock.company_disclosures" in report_text

        state_log_path = (
            Path(config["results_dir"])
            / normalized
            / "TradingAgentsStrategy_logs"
            / "full_states_log_2026-06-25.json"
        )
        assert state_log_path.exists()
        state_log = json.loads(state_log_path.read_text(encoding="utf-8"))
        assert state_log["company_of_interest"] == "7203.T"
        assert state_log["benchmark_ticker"] == "^N225"
        assert "phase4_yfinance_mock.market_context" in state_log["market_report"]

        audit_lines = Path(config["audit_log_path"]).read_text(encoding="utf-8").splitlines()
        assert len(audit_lines) == 1
        audit_record = json.loads(audit_lines[0])
        assert audit_record["ticker"] == "7203.T"
        assert audit_record["benchmark"] == "^N225"
        assert audit_record["execution_mode"] == "research_only"
        assert "keeps the .T suffix through the workflow" in audit_record["main_reasons"]
        assert "phase4_yfinance_mock.company_disclosures" in audit_record["next_checkpoints"]

        memory_entries = mock_graph.memory_log.load_entries()
        assert len(memory_entries) == 1
        assert memory_entries[0]["ticker"] == "7203.T"
        assert memory_entries[0]["pending"] is True
    finally:
        set_config(before)
