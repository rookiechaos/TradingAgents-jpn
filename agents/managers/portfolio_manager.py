"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
portfolio decision directly, in a single call. Japan-equity runs use a
stricter schema that requires the investment-committee fields from the PRD;
global runs keep those fields optional. The result is rendered back to
markdown for storage in ``final_trade_decision`` so memory log, CLI display,
and saved reports continue to consume the same shape they do today. When a
provider does not expose structured output, the agent falls back gracefully to
free-text generation.
"""

from __future__ import annotations

from tradingagents.agents.schemas import (
    JapanPortfolioDecision,
    PortfolioDecision,
    render_pm_decision,
)
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
    get_market_profile,
    get_market_profile_instruction,
    get_research_only_notice,
)
from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_with_metadata_or_freetext,
)


def create_portfolio_manager(llm):
    def portfolio_manager_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)
        is_jp_mode = get_market_profile() == "jp_equity"
        decision_schema = JapanPortfolioDecision if is_jp_mode else PortfolioDecision
        structured_llm = bind_structured(llm, decision_schema, "Portfolio Manager")

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- Lessons from prior decisions and outcomes:\n{past_context}\n"
            if past_context
            else ""
        )

        committee_instruction = ""
        if is_jp_mode:
            committee_instruction = """
Always fill the Japanese investment-committee fields:
- 投資判断: 買い / 中立 / 売り
- 確信度
- 主要根拠
- 反対意見
- 最大リスク
- 次に確認すべき材料"""

        prompt = f"""As the Portfolio Manager, synthesize the risk analysts' debate and deliver the final trading decision.

{instrument_context}

---

This workflow is for research support only. {get_research_only_notice()}

**Rating Scale** (use exactly one):
- **Buy**: Strong conviction to enter or add to position
- **Overweight**: Favorable outlook, gradually increase exposure
- **Hold**: Maintain current position, no action needed
- **Underweight**: Reduce exposure, take partial profits
- **Sell**: Exit position or avoid entry

**Context:**
- Research Manager's investment plan: **{research_plan}**
- Trader's transaction proposal: **{trader_plan}**
{lessons_line}
**Risk Analysts Debate History:**
{history}

---

Be decisive and ground every conclusion in specific evidence from the analysts.
{committee_instruction}
Do not propose or imply automatic order execution; produce a research recommendation only.{get_market_profile_instruction()}{get_language_instruction()}"""

        final_trade_decision, final_trade_decision_structured, used_structured_path = (
            invoke_structured_with_metadata_or_freetext(
                structured_llm,
                llm,
                prompt,
                render_pm_decision,
                "Portfolio Manager",
            )
        )

        new_risk_debate_state = {
            "judge_decision": final_trade_decision,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_trade_decision,
            "final_trade_decision_structured": final_trade_decision_structured,
            "final_trade_decision_is_structured": used_structured_path,
        }

    return portfolio_manager_node
