"""Repeatable offline structural/financial constraint evaluation, not live-model accuracy."""

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.ai.intake import extract_brief
from app.ai.workspace import interpret
from app.services.demo import fictional_workspace
from app.services.scenarios import simulate

CASES = Path(__file__).resolve().parents[1] / "tests/fixtures/planning_eval.json"


def evaluate_case(case):
    text = case["text"].format(date=date.today() + timedelta(days=120))
    if case["kind"] == "brief":
        result = extract_brief(text)
        assert result.source == "offline"
        assert (result.preview is not None) == case["ready"]
        for key, expected in case["fields"].items():
            assert getattr(result.fields, key) == expected
        if result.preview:
            assert sum(line.amount for line in result.preview.budget_lines) == result.fields.budget
            assert result.preview.timeline and result.preview.vendors
        else:
            assert result.missing and result.questions
    else:
        base = fictional_workspace(uuid4())
        before = base.model_dump_json()
        result = interpret(text, base, None)
        assert (result.parameters.type if result.parameters else None) == case["type"]
        if result.parameters:
            for key, expected in case["values"].items():
                assert getattr(result.parameters, key) == expected
            _, scenario = simulate(base, result.parameters, uuid4(), datetime.now(UTC))
            assert scenario.original_budget == base.budget_summary
            assert scenario.proposed_budget.reconciled
            if case["type"] == "category_cost":
                assert scenario.proposed_budget.projected_cost > scenario.original_budget.projected_cost
        assert base.model_dump_json() == before
    return {"name": case["name"], "kind": case["kind"], "constraints_passed": True}


def evaluate():
    results = [evaluate_case(case) for case in json.loads(CASES.read_text(encoding="utf-8"))]
    return {
        "mode": "deterministic offline constraints; no live-provider accuracy claim",
        "passed": len(results),
        "total": len(results),
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
