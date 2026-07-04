import unittest

import pytest

from cli.utils import normalize_ticker_symbol
from tradingagents.agents.utils.agent_utils import build_instrument_context


@pytest.mark.unit
class TickerSymbolHandlingTests(unittest.TestCase):
    def test_normalize_ticker_symbol_preserves_exchange_suffix(self):
        self.assertEqual(normalize_ticker_symbol(" cnc.to "), "CNC.TO")

    def test_normalize_ticker_symbol_autofills_tokyo_suffix_in_jp_mode(self):
        self.assertEqual(normalize_ticker_symbol("7203"), "7203.T")

    def test_normalize_ticker_symbol_respects_runtime_non_jp_config(self):
        self.assertEqual(
            normalize_ticker_symbol(
                "0700",
                config={
                    "market_profile": "global",
                    "auto_suffix_for_plain_jp_tickers": True,
                    "default_exchange_suffix": ".T",
                },
            ),
            "0700",
        )

    def test_build_instrument_context_mentions_exact_symbol(self):
        context = build_instrument_context("7203.T")
        self.assertIn("7203.T", context)
        self.assertIn("exchange suffix", context)

    def test_single_get_ticker_no_shadow(self):
        # Regression: cli/main.py had a duplicate get_ticker with an empty
        # questionary prompt (rendered as a bare "?") that shadowed the
        # descriptive one in cli/utils. Keep a single canonical definition.
        import cli.main
        import cli.utils
        self.assertIs(cli.main.get_ticker, cli.utils.get_ticker)


if __name__ == "__main__":
    unittest.main()
