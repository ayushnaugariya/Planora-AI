"""Grounded quote context, explicit uncertainty and editable professional drafts."""

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.ai.gemini import LLM
from app.ai.negotiation import strategy
from app.core.errors import WorkspaceNotFound
from app.schemas.negotiation import NegotiationFacts, NegotiationInput, NegotiationResult
from app.schemas.workspaces import EventWorkspace, VendorState
from app.services.quote_analysis import analyze_quote

TACTICS = {
    "scope_options": "Ask for clearly priced scope options without removing essential services.",
    "itemized_total": "Request an itemized all-in total including taxes, fees and overtime.",
    "payment_schedule": "Request explicit deposit amounts, due dates and cancellation/refund conditions.",
    "package_options": "Ask whether a revised package is possible; no discount is assumed.",
    "equivalent_scope": "Compare offers only after matching inclusions, currency and contractual terms.",
    "protect_access": "Preserve accessibility, dietary requirements and essential service quality.",
    "confirm_terms": "Ask for written confirmation before agreeing to any revised terms.",
}
MESSAGE_TACTICS = {
    "scope_options": "Could you offer clearly priced alternatives while retaining essential services?",
    "itemized_total": "Please include an itemized all-in total covering taxes, fees and overtime.",
    "payment_schedule": "Please set out deposit amounts, due dates and cancellation/refund conditions.",
    "package_options": "Please outline package alternatives, without assuming a discount is available.",
    "equivalent_scope": "Please clarify the inclusions and terms so we can compare equivalent scope.",
    "protect_access": "Please preserve our dietary/access requirements and essential service quality.",
    "confirm_terms": "Could you confirm proposed terms in writing before we make a decision?",
}
REQUESTS = {
    "lower_price": (
        "Could you review the quotation and suggest a lower all-in price or clearly priced scope options?"
    ),
    "additional_services": (
        "Could you outline any additional services you could include within the "
        "same quoted total, without reducing the quoted scope?"
    ),
    "package_discount": (
        "Would you consider a package discount or a revised bundle? Please show any "
        "changes to inclusions separately."
    ),
    "payment_terms": (
        "Could you propose a clear payment schedule, with deposit amounts, due "
        "dates, and cancellation/refund conditions? No revised terms have been "
        "agreed."
    ),
    "hidden_charges": (
        "Please itemize the all-in total and clarify taxes, service fees, travel, "
        "setup, overtime and any exclusions or additional charges."
    ),
    "compare_offers": (
        "We are comparing supplied offers, subject to matching their scope and "
        "terms. Could you confirm your best all-in proposal and what it includes?"
    ),
    "custom_package": (
        "Could you propose a customized package around our event requirements, "
        "itemizing each inclusion and any change in price?"
    ),
}


def vendor_for(base: EventWorkspace, vendor_id: UUID) -> VendorState:
    vendor = next((v for v in base.vendors if v.id == vendor_id), None)
    if vendor is None:
        raise WorkspaceNotFound
    return vendor


def context(
    base: EventWorkspace, vendor_id: UUID, body: NegotiationInput
) -> tuple[NegotiationFacts, list[str], list[str]]:
    vendor = vendor_for(base, vendor_id)
    category = base.plan.vendors[vendor.group_index]
    missing, warnings, scope, terms, comparisons = [], [], [], {}, []
    quoted, source = None, "No recorded quotation"
    seen_sources = set()
    if len(set(body.comparison_expense_ids)) != len(body.comparison_expense_ids):
        raise HTTPException(status_code=422, detail="Comparison expense IDs must be distinct")
    candidates = [
        e
        for e in base.expenses
        if not e.cancelled
        and e.category_key == category.key
        and e.vendor_id in (None, vendor.id)
        and e.quoted_amount is not None
    ]
    if body.expense_id:
        item = next((e for e in candidates if e.id == body.expense_id), None)
        if item is None:
            raise HTTPException(
                status_code=404, detail="Choose an active quote in this event/vendor category"
            )
    else:
        linked = [e for e in candidates if e.vendor_id == vendor.id]
        item = linked[0] if len(linked) == 1 else None
        if len(linked) > 1 and body.source is None:
            missing.append("Select the specific saved expense quotation; several are linked to this vendor.")
    if item:
        quoted, source = item.quoted_amount, f"Saved expense: {item.description}"
        scope = [item.description]
        if item.vendor_id is None:
            warnings.append(
                "The selected category expense is not linked to this vendor; confirm the association."
            )
    if body.vendor_quote_id:
        legacy = next((q for q in vendor.quotes if q.id == body.vendor_quote_id), None)
        if legacy is None:
            raise HTTPException(status_code=404, detail="Quote is not in this vendor record")
        if body.expense_id or body.source:
            raise HTTPException(status_code=422, detail="Choose one primary quotation source")
        quoted, source = Decimal(legacy.amount), "Saved vendor quotation"
        scope = [legacy.note] if legacy.note else []
    elif quoted is None and body.source is None and len(vendor.quotes) == 1:
        quoted, source = Decimal(vendor.quotes[0].amount), "Saved vendor quotation"
        scope = [vendor.quotes[0].note] if vendor.quotes[0].note else []
    if body.source:
        q = body.source
        if (
            q.revision != base.revision
            or q.category_key != category.key
            or q.vendor_id not in (None, vendor.id)
        ):
            raise HTTPException(
                status_code=422, detail="Analyzed source must match this revision/vendor category"
            )
        analysis = analyze_quote(base, q)
        seen_sources.add(analysis.source_hash)
        if not analysis.importable:
            missing.extend(
                analysis.issues
                + ["Resolve the primary quote's currency, tax/fee and all-in price in Quote Analyzer."]
            )
        else:
            quoted, source = (
                analysis.comparable_total,
                "User-supplied analyzed quote (not recorded in ledger)",
            )
            scope = [line.description for line in analysis.items][:8]
            if analysis.terms.get("inclusions"):
                scope.append(analysis.terms["inclusions"])
            terms = analysis.terms
            warnings.extend(f"Primary quote: missing {label}." for label in analysis.missing)
    for expense_id in body.comparison_expense_ids:
        other = next(
            (
                e
                for e in base.expenses
                if e.id == expense_id
                and not e.cancelled
                and e.category_key == category.key
                and e.quoted_amount is not None
            ),
            None,
        )
        if other is None or (item and other.id == item.id):
            raise HTTPException(
                status_code=422, detail="Choose another owned quoted expense in the same category"
            )
        comparisons.append(
            f"{other.description}: {other.quoted_amount} {base.details.currency} "
            "(recorded quote; scope equivalence unverified)."
        )
    for q in body.comparisons:
        if q.revision != base.revision or q.category_key != category.key:
            raise HTTPException(
                status_code=422, detail="Comparison sources must match this revision and category"
            )
        if q.vendor_id is not None and q.vendor_id not in {v.id for v in base.vendors}:
            raise HTTPException(status_code=404, detail="Comparison vendor is not in this event")
        if q.vendor_id is not None:
            comparison_vendor = vendor_for(base, q.vendor_id)
            if base.plan.vendors[comparison_vendor.group_index].key != category.key:
                raise HTTPException(status_code=422, detail="Comparison vendor category must match")
        analysis = analyze_quote(base, q)
        if analysis.source_hash in seen_sources:
            raise HTTPException(status_code=422, detail="Reuse distinct quote sources for comparison")
        seen_sources.add(analysis.source_hash)
        if analysis.comparable_total is None or analysis.currency is None:
            missing.append("Comparison quotation needs a valid all-in total and explicit currency.")
        else:
            comparisons.append(
                f"{analysis.vendor_name or analysis.filename}: {analysis.comparable_total} "
                f"{analysis.currency}; supplied offer, scope/terms equivalence unverified."
            )
            warnings.extend(analysis.issues)
    if not vendor.name.strip():
        missing.append("Add this vendor's name in Edit vendor details before addressing a draft.")
    if quoted is None:
        missing.append("Select a recorded quoted expense or reuse a priced source from Quote Analyzer.")
    if body.scenario == "compare_offers" and not comparisons:
        missing.append(
            "Select another recorded quotation or reuse multiple analyzed quote sources for comparison."
        )
    reduction = (
        max(Decimal(0), quoted - body.target_price)
        if quoted is not None and body.target_price is not None
        else None
    )
    if body.target_price is not None and quoted is not None and body.target_price >= quoted:
        warnings.append("Target is not below the quotation; no price reduction is implied.")
    obligations = [
        f"{e.description}: committed {e.committed_amount}; paid {e.paid_amount} {e.currency}."
        for e in base.expenses
        if e.vendor_id == vendor.id and (e.committed_amount or e.paid_amount)
    ]
    protected = [
        (
            "Existing commitments, paid amounts, essential scope and cancellation "
            "obligations are not released by a draft."
        ),
        "Preserve dietary/access requirements and essential service quality; confirm revisions in writing.",
    ] + obligations
    if base.details.accessibility_requirements:
        protected.append("Recorded access requirements: " + base.details.accessibility_requirements)
    if base.details.dietary:
        protected.append("Recorded dietary preferences: " + ", ".join(base.details.dietary))
    facts = NegotiationFacts(
        vendor_name=vendor.name,
        category=category.label,
        currency=base.details.currency,
        quote=quoted,
        quote_source=source,
        target=body.target_price,
        requested_reduction=reduction,
        counteroffer=body.target_price if quoted is not None else None,
        event_budget=Decimal(base.details.budget),
        category_allowance=Decimal(
            next(line.amount for line in base.plan.budget_lines if line.key == category.key)
        ),
        scope=scope,
        terms=terms,
        comparisons=comparisons,
        protected=protected,
    )
    warnings += [
        (
            "All quotations/terms are user-entered, not independently verified. No "
            "market rate or availability is inferred."
        ),
        (
            "Requested reductions are unagreed potential savings, not achieved savings. "
            "Drafts never change your budget or send a message."
        ),
    ]
    return facts, list(dict.fromkeys(missing)), list(dict.fromkeys(warnings))


def generate(
    base: EventWorkspace, vendor_id: UUID, body: NegotiationInput, client: LLM | None = None
) -> NegotiationResult:
    facts, missing, warnings = context(base, vendor_id, body)
    if missing:
        return NegotiationResult(
            event_id=base.id,
            vendor_id=vendor_id,
            revision=base.revision,
            facts=facts,
            missing=missing,
            warnings=warnings,
            source="offline",
            approach="Complete the missing recorded facts first.",
            suggestions=[],
            message=None,
        )
    selected, source = strategy(base, body, facts, client)
    opening = [
        "Thank you for your quotation",
        "I am following up on your proposal",
        "Thank you for sharing the proposal",
    ][body.variant]
    event_label = base.details.event_type.replace("_", " ")
    location = f" in {base.details.city}" if base.details.city else ""
    lines = [
        f"Hello {facts.vendor_name},",
        "",
        f"{opening} of {facts.quote} {facts.currency} for {facts.category.lower()} "
        f"for our {event_label} on {base.details.event_date.isoformat()}{location}.",
        "",
        REQUESTS[body.scenario],
    ]
    if facts.target is not None:
        lines.append(
            f"Our requested target is {facts.target} {facts.currency}. "
            "Could you let us know whether this is possible and explain any scope changes? "
            "This is a request, not an agreed price."
        )
    if facts.scope:
        lines.append(
            "Please preserve the quoted scope, including: "
            + "; ".join(facts.scope)
            + ". Confirm any exclusions separately."
        )
    if body.instruction:
        lines.append("Additional request for your consideration (user supplied): " + body.instruction)
    for tactic in selected.tactics:
        lines.append(MESSAGE_TACTICS[tactic])
    lines += [
        (
            "Please confirm proposed changes in writing before we consider agreeing. "
            "Any existing obligations remain in place; this request does not release them."
        ),
        "",
        "Thank you for considering our request." if selected.tone == "cordial" else "Thank you.",
    ]
    return NegotiationResult(
        event_id=base.id,
        vendor_id=vendor_id,
        revision=base.revision,
        facts=facts,
        missing=[],
        warnings=warnings,
        source=source,
        approach=(
            "A professional request grounded in the selected quote; "
            "seek written alternatives without assuming concessions."
        ),
        suggestions=[TACTICS[t] for t in selected.tactics],
        message="\n".join(lines),
    )
