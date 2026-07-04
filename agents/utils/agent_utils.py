import functools
import logging
import re
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)

_LAZY_TOOL_EXPORTS = {
    "get_stock_data": "tradingagents.agents.utils.core_stock_tools",
    "get_indicators": "tradingagents.agents.utils.technical_indicators_tools",
    "get_fundamentals": "tradingagents.agents.utils.fundamental_data_tools",
    "get_balance_sheet": "tradingagents.agents.utils.fundamental_data_tools",
    "get_cashflow": "tradingagents.agents.utils.fundamental_data_tools",
    "get_income_statement": "tradingagents.agents.utils.fundamental_data_tools",
    "get_news": "tradingagents.agents.utils.news_data_tools",
    "get_insider_transactions": "tradingagents.agents.utils.news_data_tools",
    "get_global_news": "tradingagents.agents.utils.news_data_tools",
    "get_japan_company_disclosures": "tradingagents.agents.utils.japan_market_tools",
    "get_japan_earnings_digest": "tradingagents.agents.utils.japan_market_tools",
    "get_japan_macro_indicators": "tradingagents.agents.utils.japan_market_tools",
    "get_japan_market_context": "tradingagents.agents.utils.japan_market_tools",
    "get_verified_market_snapshot": "tradingagents.agents.utils.market_data_validation_tools",
}


def __getattr__(name: str):
    if name not in _LAZY_TOOL_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(_LAZY_TOOL_EXPORTS[name])
    value = getattr(module, name)
    globals()[name] = value
    return value


def get_market_profile() -> str:
    from tradingagents.dataflows.config import get_config

    return str(get_config().get("market_profile", "global")).strip().lower()


def get_market_profile_from_config(config: Optional[Mapping[str, Any]] = None) -> str:
    cfg = config or {}
    return str(cfg.get("market_profile", "global")).strip().lower()


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Applied to every agent whose output reaches the saved report —
    analysts, researchers, debaters, research manager, trader, and
    portfolio manager — so a non-English run produces a fully localized
    report rather than a mix of languages.
    """
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def get_research_only_notice() -> str:
    from tradingagents.dataflows.config import get_config

    return str(get_config().get("research_only_notice", "")).strip()


def get_market_profile_instruction() -> str:
    from tradingagents.dataflows.config import get_config

    cfg = get_config()
    if get_market_profile() != "jp_equity":
        return ""
    benchmark = cfg.get("default_benchmark", "^N225")
    locale = cfg.get("report_locale", "ja-JP")
    currency = cfg.get("currency_display", "JPY")
    return (
        " This run is in Japan equity mode. Prioritize Tokyo-listed company context, "
        f"use {benchmark} or configured Japanese benchmarks when comparing market direction, "
        f"present dates and wording in a {locale} business style, and prefer {currency} / 円 "
        "when discussing prices, market cap, or financial statements."
    )


def get_localized_report_header(
    ticker: str,
    trade_date: str,
    benchmark: str,
    config: Optional[Mapping[str, Any]] = None,
) -> str:
    notice = (
        str(config.get("research_only_notice", "")).strip()
        if config is not None
        else get_research_only_notice()
    )
    profile = (
        get_market_profile_from_config(config)
        if config is not None
        else get_market_profile()
    )
    if profile == "jp_equity":
        return "\n".join([
            f"# 日本株投資委員会レポート: {ticker}",
            "",
            f"- 分析日: {trade_date}",
            f"- ベンチマーク: {benchmark}",
            f"- 実行モード: 調査専用",
            f"- 免責: {notice}",
        ])
    return "\n".join([
        f"# Trading Analysis Report: {ticker}",
        "",
        f"- Analysis Date: {trade_date}",
        f"- Benchmark: {benchmark}",
        "- Execution Mode: research_only",
        f"- Disclaimer: {notice}",
    ])


def extract_markdown_section(text: str, label: str) -> str:
    """Extract a markdown section value, including multi-line bodies.

    Supports both:
    - ``**Label**: single-line value``
    - ``**Label**: first line`` followed by additional wrapped lines / bullets
    - ``Label: ...`` / ``Label：...``
    - ``### Label`` headings followed by wrapped lines / bullets

    Extraction stops at the next markdown header of the same ``**Label**:`` form
    or the end of the text.
    """
    patterns = [
        (
            rf"^\*\*{re.escape(label)}\*\*:\s*(.*?)"
            rf"(?=^\*\*[^*\n]+\*\*:\s|^\*\*[^*\n]+\*\*：|^###\s+|\Z)"
        ),
        (
            rf"^{re.escape(label)}[：:]\s*(.*?)"
            rf"(?=^[^\n:：]{1,60}[：:]|^###\s+|\Z)"
        ),
        (
            rf"^###\s*{re.escape(label)}\s*$\n?(.*?)"
            rf"(?=^###\s+|\Z)"
        ),
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


def _clean_identity_value(value: Any) -> Optional[str]:
    """Return a trimmed string, or None for empty / placeholder-ish values."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"none", "n/a", "nan", "null"}:
        return None
    return cleaned


@functools.lru_cache(maxsize=256)
def resolve_instrument_identity(ticker: str) -> dict:
    """Resolve deterministic identity metadata (company name, sector, …) for a ticker.

    This exists to stop the pipeline from hallucinating a *different* company
    when a chart pattern suggests a different industry than the real one
    (#814): without a ground-truth name, the market analyst would pattern-match
    the price action to a narrative and invent an identity that then cascaded
    through every downstream agent.

    Best-effort by design: if yfinance is unavailable, rate-limited, or doesn't
    recognise the ticker, we return ``{}`` and the caller falls back to
    ticker-only context rather than failing before analysis starts. Cached so
    the lookup happens at most once per ticker per process.
    """
    try:
        import yfinance as yf

        info = yf.Ticker(ticker.upper()).info or {}
    except Exception as exc:  # noqa: BLE001 — fail open, never block the run
        logger.debug("Could not resolve instrument identity for %s: %s", ticker, exc)
        return {}

    identity: dict[str, str] = {}
    company_name = _clean_identity_value(info.get("longName")) or _clean_identity_value(
        info.get("shortName")
    )
    if company_name:
        identity["company_name"] = company_name
    for source_key, target_key in (
        ("sector", "sector"),
        ("industry", "industry"),
        ("exchange", "exchange"),
        ("quoteType", "quote_type"),
    ):
        value = _clean_identity_value(info.get(source_key))
        if value:
            identity[target_key] = value
    return identity


def build_instrument_context(
    ticker: str,
    asset_type: str = "stock",
    identity: Optional[Mapping[str, str]] = None,
) -> str:
    """Describe the exact instrument so agents preserve identity and ticker.

    When ``identity`` is provided (resolved deterministically via
    :func:`resolve_instrument_identity`), the company name and business
    classification are injected so agents anchor to the real company rather
    than pattern-matching the price chart to a wrong one (#814).
    """
    is_crypto = asset_type == "crypto"
    instrument_label = "asset" if is_crypto else "instrument"
    context = (
        f"The {instrument_label} to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`, `-USD`)."
    )

    details = []
    if identity:
        name = identity.get("company_name") or identity.get("name")
        if name:
            details.append(f"{'Name' if is_crypto else 'Company'}: {name}")
        sector, industry = identity.get("sector"), identity.get("industry")
        if sector and industry:
            details.append(f"Business classification: {sector} / {industry}")
        elif sector:
            details.append(f"Sector: {sector}")
        elif industry:
            details.append(f"Industry: {industry}")
        if identity.get("exchange"):
            details.append(f"Exchange: {identity['exchange']}")

    if details:
        context += (
            f" Resolved identity: {'; '.join(details)}. "
            "Do not substitute a different company or ticker unless a tool "
            "result explicitly disproves this resolved identity."
        )

    if is_crypto:
        context += (
            " Treat it as a crypto asset rather than a company, and do not "
            "assume company fundamentals are available."
        )
    return context


def get_instrument_context_from_state(state: Mapping[str, Any]) -> str:
    """Return the instrument context for the current run.

    Prefers the identity-resolved context computed once at run start and
    stored on the state (see ``TradingAgentsGraph.resolve_instrument_context``).
    Falls back to a ticker-only context — with no network lookup — when the
    state was constructed without it (bare programmatic states, tests), so a
    consumer is never forced to make a yfinance call mid-graph.
    """
    context = state.get("instrument_context")
    if isinstance(context, str) and context.strip():
        return context
    return build_instrument_context(
        str(state["company_of_interest"]),
        state.get("asset_type", "stock"),
    )


def create_msg_delete():
    from langchain_core.messages import HumanMessage, RemoveMessage

    def delete_messages(state):
        """Clear messages and add a context-anchored placeholder.

        The placeholder must not be a bare ``"Continue"``: some
        OpenAI-compatible providers interpret that literally as the user task
        and produce output about the word "continue" instead of analysing the
        instrument (#888). Anchoring it to the resolved instrument context and
        date keeps the next analyst on-task even if the provider treats the
        placeholder as a standalone request.
        """
        messages = state["messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        instrument_context = get_instrument_context_from_state(state)
        trade_date = state.get("trade_date", "the requested date")
        placeholder = HumanMessage(
            content=(
                f"Proceed with your assigned analysis for this workflow. "
                f"{instrument_context} The analysis date is {trade_date}."
            )
        )
        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        
