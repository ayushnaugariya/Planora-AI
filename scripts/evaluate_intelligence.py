"""Offline structural/grounding/financial constraints, not fabricated model accuracy."""

import json
from pathlib import Path
from uuid import uuid4

from app.schemas.intelligence import DelayRequest, QuoteRequest
from app.services.decisions import decide
from app.services.demo import fictional_workspace
from app.services.design import studio
from app.services.quote_analysis import analyze_quote
from app.services.timeline_intelligence import delay_analysis

CASES = Path(__file__).resolve().parents[1] / "tests/fixtures/intelligence_eval.json"


def evaluate_case(case):
    base = fictional_workspace(uuid4())
    if case["kind"] == "timeline":
        task = next(
            item for item in base.tasks if base.plan.timeline[item.milestone_index].category != "event"
        )
        base.plan.timeline[task.milestone_index].due = base.details.event_date
    before = base.model_dump_json()
    if case["kind"] == "decision":
        result = decide(base, case["question"])
        if case["type"] is None:
            assert result.clarification and not result.recommendations
        else:
            assert result.recommendations
            for card in result.recommendations:
                assert card.evidence and card.approval_required
                assert card.preview.parameters.type == case["type"]
                assert card.preview.original_budget == base.budget_summary
                assert card.preview.proposed_budget.reconciled
                if case["type"] == "budget_reduction":
                    assert card.preview.proposed_budget.total_budget == 1499500
                    assert card.preview.proposed_budget.planned_allocation == 1499500
                elif case["type"] == "guest_count":
                    assert card.preview.proposed_values["guest_count"] == 90
                else:
                    assert card.preview.proposed_budget.projected_cost > base.budget_summary.projected_cost
    elif case["kind"] == "quote":
        result = analyze_quote(base, QuoteRequest(revision=1, category_key="venue", text=case["text"]))
        assert result.importable == case["importable"]
        assert (str(result.comparable_total) if result.comparable_total is not None else None) == case[
            "total"
        ]
        assert result.source_text == case["text"]
    elif case["kind"] == "design":
        result = studio(base, case["brief"])
        assert result.ranking_source == "offline" and result.concepts[0].style == case["style"]
        assert all(concept.budget_links for concept in result.concepts)
    else:
        result = delay_analysis(base, DelayRequest(revision=1, task_id=task.id, delay_days=1))
        assert result.impacts[0].beyond_event and result.issues and not result.can_apply
    # API outputs intentionally include read-only computed expense fields. Use
    # the model's round-trip serialization rather than accepting them as input.
    type(result).model_validate_json(result.model_dump_json(round_trip=True))
    assert base.model_dump_json() == before
    return {"name": case["name"], "passed": True}


def evaluate():
    results = [evaluate_case(case) for case in json.loads(CASES.read_text(encoding="utf-8"))]
    return {
        "mode": "offline constraints; no live-provider accuracy claim",
        "passed": len(results),
        "total": len(results),
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
