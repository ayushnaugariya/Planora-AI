"""Repeatable evaluation cases are executable regression constraints."""

import json

import pytest

from scripts.evaluate_intelligence import CASES, evaluate_case


@pytest.mark.parametrize("case", json.loads(CASES.read_text(encoding="utf-8")), ids=lambda case: case["name"])
def test_intelligence_constraint_case(case):
    assert evaluate_case(case)["passed"]
