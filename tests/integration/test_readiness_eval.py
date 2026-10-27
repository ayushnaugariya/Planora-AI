"""Readiness demonstration cases are also regression tests."""

import json

import pytest

from scripts.evaluate_readiness import CASES, evaluate_case


@pytest.mark.parametrize("case", json.loads(CASES.read_text(encoding="utf-8")), ids=lambda case: case["name"])
def test_readiness_constraint_case(case):
    assert evaluate_case(case)["passed"]
