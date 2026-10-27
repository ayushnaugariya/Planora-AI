"""The repeatable demonstration constraints run in CI alongside API regressions."""

import json

import pytest

from scripts.evaluate_planning import CASES, evaluate_case


@pytest.mark.parametrize("case", json.loads(CASES.read_text(encoding="utf-8")), ids=lambda case: case["name"])
def test_representative_planning_constraints(case):
    assert evaluate_case(case)["constraints_passed"]
