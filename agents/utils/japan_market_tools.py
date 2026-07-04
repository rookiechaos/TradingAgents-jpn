from typing import Annotated

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_japan_market_context(
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """Retrieve Japan-market macro context from the configured JP provider."""
    return route_to_vendor("get_japan_market_context", curr_date)


@tool
def get_japan_macro_indicators(
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """Retrieve Japan macro indicators from the configured JP provider."""
    return route_to_vendor("get_japan_macro_indicators", curr_date)


@tool
def get_japan_company_disclosures(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """Retrieve Japan-company disclosure context from the configured JP provider."""
    return route_to_vendor("get_japan_company_disclosures", ticker, curr_date)


@tool
def get_japan_earnings_digest(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """Retrieve Japan-company earnings digest context from the configured JP provider."""
    return route_to_vendor("get_japan_earnings_digest", ticker, curr_date)
