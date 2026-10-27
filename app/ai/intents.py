"""Small, anchored language extensions; data becomes reviewed inputs, never actions."""

import re
from decimal import Decimal

from app.schemas.budget import cents
from app.services.budget import effective_cost


def resolve(question, workspace):
    """Return a new supported command or a specific request for missing facts.

    Legacy parsing and Gemini output validation remain in workspace.interpret.
    Full matches deliberately reject appended instructions and multiple changes.
    """
    text = question.lower().strip()
    text = re.sub(r"^how can i reduce my event budget by ", "reduce the budget by ", text)
    cost_increase = re.fullmatch(
        r"what (?:happens )?if (?:my |the )?(venue|catering) cost increases by "
        r"([0-9]{1,3}(?:\.[0-9]{1,2})?)%[.!?]?",
        text,
    )
    if cost_increase:
        text = f"what if the {cost_increase[1]} costs {cost_increase[2]}% more?"
    prefix = r"(?:(?:what if (?:we |i )?|compare options if i )|(?:please ))?"
    additional = re.fullmatch(r"what if ([0-9]{1,4}) (?:additional|more) guests? (?:attend|come)[.!?]?", text)
    if additional:
        return {
            "type": "guest_count",
            "guest_count": workspace.details.guest_count + int(additional[1]),
        }, None
    money = re.fullmatch(
        r"(?:how can i )?(?:reduce|cut) (?:the )?budget by (₹|inr|usd|eur|gbp)\s*"
        r"((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,2})?)[.!?]?",
        text,
    )
    if money:
        currency = "INR" if money[1] == "₹" else money[1].upper()
        if currency != workspace.details.currency:
            return (
                None,
                f"The saved event uses {workspace.details.currency}. "
                "Supply that currency; no FX conversion is inferred.",
            )
        return {"type": "budget_reduction", "amount": money[2].replace(",", "")}, None
    increase = re.fullmatch(
        r"what if (?:the )?(venue|catering) costs? ([0-9]{1,3}(?:\.[0-9]{1,2})?)% more[.!?]?",
        text,
    )
    if increase:
        records = [
            item for item in workspace.expenses if item.category_key == increase[1] and not item.cancelled
        ]
        if len(records) != 1 or (records[0].estimate is None and records[0].quoted_amount is None):
            return (
                None,
                "Choose one saved priced expense as the percentage baseline, or supply an all-in quote.",
            )
        item = records[0]
        if item.committed_amount is not None:
            return (
                None,
                "This expense has a saved commitment. Confirm the revised obligation explicitly; "
                "a hypothetical quote cannot replace it.",
            )
        percent = Decimal(increase[2])
        if not 0 < percent <= 100:
            return None, "Supply an increase above 0% and at most 100%, or use an explicit all-in amount."
        amount = cents(effective_cost(item) * (1 + percent / 100))
        return {
            "type": "category_cost",
            "category_key": increase[1],
            "expense_id": str(item.id),
            "amount": str(amount),
        }, None
    relative = re.fullmatch(
        prefix + r"(increase|decrease|reduce) (?:the )?guest(?: count| list)? by ([0-9]{1,4})[.!?]?",
        text,
    )
    if relative:
        delta = int(relative[2]) * (1 if relative[1] == "increase" else -1)
        return {"type": "guest_count", "guest_count": workspace.details.guest_count + delta}, None
    budget = re.fullmatch(
        prefix + r"(?:reduce|cut) (?:the )?budget by ([0-9]+(?:\.[0-9]+)?)\s*(%)[.!?]?", text
    )
    if budget:
        return {"type": "budget_reduction", "percent": budget[1]}, None
    day = re.fullmatch(
        r"(?:move (?:the )?event to|change (?:the )?(?:event )?date to|"
        r"what if (?:the )?event date changes to) ([0-9]{4}-[0-9]{2}-[0-9]{2})[.!?]?",
        text,
    )
    if day:
        return {"type": "event_date", "event_date": day[1]}, None
    quote = re.fullmatch(
        r"(?:change|set) (?:the )?(venue|catering) (?:cost|quote) to ([0-9]+(?:\.[0-9]{1,2})?)[.!?]?",
        text,
    )
    if quote:
        expenses = [
            item for item in workspace.expenses if item.category_key == quote[1] and not item.cancelled
        ]
        if len(expenses) > 1:
            return (
                None,
                "Which saved expense should this quote replace? Select its record in Scenario Studio.",
            )
        return {
            "type": "category_cost",
            "category_key": quote[1],
            "amount": quote[2],
            "expense_id": str(expenses[0].id) if expenses else None,
        }, None
    if "compare" in text and any(word in text for word in ("quotes", "catering", "venue")):
        return None, (
            "Which two all-in quote amounts, currency and saved expense should be compared? "
            "Use Compare written quotes below; each option becomes a separate reviewed preview."
        )
    if any(
        phrase in text
        for phrase in ("date changes", "change the date", "change event date", "move the event")
    ):
        return (
            None,
            "Which exact date do you want to explore? Use YYYY-MM-DD; booked suppliers must reconfirm.",
        )
    if re.search(r"\b(?:increase|decrease)\b.*\bguests?\b", text):
        return None, "How many guests in total, or by how many should the saved headcount change?"
    return None, None
