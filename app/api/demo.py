"""Read-only fictional illustration calculated by the same financial/scenario services."""

from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, HTTPException, Request
from pydantic import Field

from app.api.dependencies import Owner, repository
from app.schemas.budget import BudgetInput
from app.schemas.rescue import RescueAssessment, RescueRequest
from app.schemas.workspaces import EventWorkspace, RevisionEntry
from app.services.demo import fictional_workspace
from app.services.rescue import assess

router = APIRouter(tags=["demo"])


class Demo(BudgetInput):
    fictional: Literal[True] = True
    label: str
    workspace: EventWorkspace
    rescue: RescueAssessment


@router.get("/api/demo", response_model=Demo)
def illustration():
    event = fictional_workspace(uuid5(NAMESPACE_URL, "planora:fictional-demo"))
    vendor = next(
        item for item in event.vendors if event.plan.vendors[item.group_index].key == "entertainment"
    )
    rescue = assess(
        event,
        RescueRequest(
            revision=1,
            request_id=uuid5(NAMESPACE_URL, "planora:fictional-rescue"),
            kind="vendor_cancellation",
            description="The entertainment supplier cancels before the gathering.",
            vendor_id=vendor.id,
            cancellation_fee="100",
            quotes=[
                {"label": "Smaller acoustic set", "amount": "950", "confirmed": True},
                {"label": "Replacement music package", "amount": "1250", "confirmed": True},
            ],
        ),
    )
    return Demo(
        label="Fictional example; no real quotes, availability, bookings or saved events",
        workspace=event,
        rescue=rescue,
    )


class DemoCreate(BudgetInput):
    request_id: UUID
    acknowledge_fictional: bool = Field(strict=True)


@router.post("/api/demo/workspace", response_model=EventWorkspace, status_code=201)
def create_demo(body: DemoCreate, request: Request, owner: Owner):
    if not body.acknowledge_fictional:
        raise HTTPException(status_code=422, detail="Confirm this is a new fictional workspace")
    event = fictional_workspace(uuid5(NAMESPACE_URL, f"planora:demo:{owner}:{body.request_id}"))
    event.details.title = event.plan.title = "Fictional · Garden celebration"
    event.details.assumptions = "Fictional prices and supplier confirmations for demonstration only."
    venue = next(item for item in event.expenses if item.category_key == "venue")
    venue.committed_amount, venue.paid_amount = venue.estimate, venue.estimate / 2
    event.history = [
        RevisionEntry(
            revision=1,
            created_at=event.created_at,
            summary="Explicitly created a separate fictional demo; prices are illustrative",
        )
    ]
    return repository(request).create(owner, event, if_absent=True)
