from __future__ import annotations

import json
from pathlib import Path

import pytest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "phase4_yfinance_mock" / "jp_equities_yfinance_mock.json"


@pytest.mark.unit
def test_phase4_yfinance_mock_fixture_contains_five_japanese_equities():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    records = payload["records"]
    assert payload["fixture_type"] == "phase4_yfinance_mock"
    assert len(records) == 5
    assert {record["ticker"] for record in records} == {
        "7203.T",
        "6758.T",
        "9984.T",
        "8306.T",
        "7974.T",
    }


@pytest.mark.unit
def test_phase4_yfinance_mock_fixture_records_have_expected_fields():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    required = {
        "ticker",
        "company_name",
        "exchange",
        "currency",
        "benchmark",
        "identity",
        "ohlcv_sample",
        "fundamentals",
        "news_items",
        "phase4_mock_note",
    }
    for record in payload["records"]:
        assert required.issubset(record.keys())
        assert record["ticker"].endswith(".T")
        assert record["benchmark"] == "^N225"
        assert len(record["ohlcv_sample"]) >= 3
        assert len(record["news_items"]) >= 1
