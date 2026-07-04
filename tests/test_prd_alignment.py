from __future__ import annotations

import pytest
from pydantic import ValidationError

from tradingagents.agents.schemas import (
    JapanPortfolioDecision,
    PortfolioDecision,
    PortfolioRating,
    render_pm_decision,
)
from tradingagents.default_config import DEFAULT_CONFIG


@pytest.mark.unit
def test_prd_default_jp_profile_contract():
    assert DEFAULT_CONFIG["market_profile"] == "jp_equity"
    assert DEFAULT_CONFIG["output_language"] == "Japanese"
    assert DEFAULT_CONFIG["default_exchange_suffix"] == ".T"
    assert DEFAULT_CONFIG["default_benchmark"] == "^N225"
    assert "^TOPX" in DEFAULT_CONFIG["jp_benchmark_candidates"]
    assert DEFAULT_CONFIG["trade_execution_mode"] == "research_only"
    assert "投資助言ではありません" in DEFAULT_CONFIG["research_only_notice"]
    assert DEFAULT_CONFIG["benchmark_map"][".T"] == "^N225"


@pytest.mark.unit
def test_prd_global_portfolio_decision_does_not_require_japanese_committee_fields():
    decision = PortfolioDecision(
        rating=PortfolioRating.HOLD,
        executive_summary="Hold while waiting for a clearer catalyst.",
        investment_thesis="The evidence is balanced.",
    )

    rendered = render_pm_decision(decision)
    assert "**Rating**: Hold" in rendered
    assert "**投資判断**" not in rendered
    assert "**主要根拠**" not in rendered


@pytest.mark.unit
def test_prd_jp_portfolio_decision_requires_committee_fields():
    with pytest.raises(ValidationError):
        JapanPortfolioDecision(
            rating=PortfolioRating.HOLD,
            executive_summary="Hold while waiting for a clearer catalyst.",
            investment_thesis="The evidence is balanced.",
        )

    decision = JapanPortfolioDecision(
        rating=PortfolioRating.BUY,
        executive_summary="Build a starter position after internal review.",
        investment_thesis="Evidence supports a constructive Japan equity view.",
        investment_judgment="買い",
        confidence="高",
        key_reasons="収益改善と株主還元が支え。",
        counterarguments="外需減速なら前提が弱まる。",
        biggest_risk="会社計画の下方修正。",
        next_checkpoints="次回決算と為替前提。",
    )

    rendered = render_pm_decision(decision)
    assert "**投資判断**: 買い" in rendered
    assert "**確信度**: 高" in rendered
    assert "**次に確認すべき材料**: 次回決算と為替前提。" in rendered


@pytest.mark.unit
def test_prd_phase4_mock_vendor_is_explicit_and_non_default():
    assert DEFAULT_CONFIG["data_vendors"]["japan_market_data"] == "jp_placeholder"
    assert "phase4_yfinance_mock" not in DEFAULT_CONFIG["data_vendors"].values()
