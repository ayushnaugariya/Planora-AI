"""A bounded labeled-text parser, not a general document reader or an AI instruction path."""

import hashlib
from datetime import date
from decimal import Decimal

from pydantic import TypeAdapter, ValidationError

from app.schemas.budget import ExpenseRecord, Money, Quantity
from app.schemas.intelligence import PaymentMilestone, QuoteAnalysis, QuoteImport, QuoteLine, QuoteRequest
from app.schemas.workspaces import EventWorkspace

MONEY, QUANTITY = TypeAdapter(Money), TypeAdapter(Quantity)
FIELDS = {
    "vendor",
    "currency",
    "tax",
    "fee",
    "all-in total",
    "deposit",
    "cancellation",
    "overtime",
    "valid until",
    "payment",
    "inclusions",
    "service",
    "subtotal",
}


def analyze_quote(base: EventWorkspace, body: QuoteRequest | QuoteImport) -> QuoteAnalysis:
    issues, values, evidence, items, payments = [], {}, {}, [], []
    for number, line in enumerate(body.text.splitlines(), 1):
        if not line.strip():
            continue
        label, separator, value = line.partition(":")
        label, value = label.strip().lower(), value.strip()
        if not separator or label not in FIELDS | {"item"}:
            issues.append(f"Line {number}: unsupported label; only documented fields are interpreted.")
            continue
        source = f"Line {number}: {line}"
        if label == "item":
            try:
                description, quantity, unit = (part.strip() for part in value.split("|"))
                record = ExpenseRecord(
                    event_id=base.id,
                    category_key=body.category_key,
                    description=description,
                    currency=base.details.currency,
                    quantity=QUANTITY.validate_python(quantity),
                    unit_amount=MONEY.validate_python(unit),
                )
                items.append(
                    QuoteLine(
                        description=record.description,
                        quantity=record.quantity,
                        unit_price=record.unit_amount,
                        total=record.line_total,
                        source=source,
                    )
                )
            except (ValueError, ValidationError):
                issues.append(f"Line {number}: expected Item: description | quantity | unit price.")
        elif label == "payment":
            try:
                due, amount = (part.strip() for part in value.split("|"))
                payments.append(
                    PaymentMilestone(
                        due=date.fromisoformat(due), amount=MONEY.validate_python(amount), source=source
                    )
                )
                values["payment"] = (values.get("payment", "") + " " + value).strip()
                evidence["payment"] = (evidence.get("payment", "") + " " + source).strip()
            except (ValueError, ValidationError):
                issues.append(f"Line {number}: expected Payment: YYYY-MM-DD | amount.")
        elif label in values:
            issues.append(f"Line {number}: duplicate {label}; ambiguity prevents recording.")
        else:
            values[label], evidence[label] = value, source
    currency = values.get("currency", "").upper()
    category = next(line for line in base.plan.budget_lines if line.key == body.category_key)
    if values.get("service") and values["service"].lower() not in {category.key, category.label.lower()}:
        issues.append(
            "Source service label differs from the selected category; confirm the correct category."
        )
    if currency not in ("INR", "USD", "EUR", "GBP"):
        if values.get("currency"):
            issues.append("Use an explicit supported currency code: INR, USD, EUR or GBP.")
        currency = None
    if currency and currency != base.details.currency:
        issues.append("Quote currency differs from the event; no FX conversion is inferred.")
    parsed = {}
    for key in ("tax", "fee", "all-in total", "deposit", "subtotal"):
        try:
            parsed[key] = MONEY.validate_python(values[key]) if key in values else None
        except ValidationError:
            parsed[key] = None
            issues.append(f"{key}: invalid nonnegative amount within supported limits.")
    subtotal = sum((item.total for item in items), Decimal("0.00")) if items else None
    if subtotal is not None and parsed["subtotal"] is not None and subtotal != parsed["subtotal"]:
        issues.append("Reported subtotal does not reconcile to the stated line items.")
    if subtotal is None:
        subtotal = parsed["subtotal"]
    if subtotal is not None and subtotal > 100_000_000:
        issues.append("Line-item subtotal exceeds the supported amount.")
        subtotal = None
    computed = None
    if subtotal is not None and parsed["tax"] is not None and parsed["fee"] is not None:
        computed = subtotal + parsed["tax"] + parsed["fee"]
    total = parsed["all-in total"] if parsed["all-in total"] is not None else computed
    if computed is not None and parsed["all-in total"] is not None and computed != total:
        issues.append("All-in total does not reconcile to line items plus stated tax and fee.")
    if total is not None and total > 100_000_000:
        issues.append("Comparable total exceeds the supported amount.")
        total = None
    if parsed["deposit"] is not None and total is not None and parsed["deposit"] > total:
        issues.append("Deposit exceeds the all-in total; confirm the terms.")
    if total is not None and sum((item.amount for item in payments), Decimal(0)) > total:
        issues.append("Payment milestones exceed the all-in total; confirm the payment schedule.")
    if "valid until" in values:
        try:
            if date.fromisoformat(values["valid until"]) < date.today():
                issues.append("Quotation validity has expired; obtain a refreshed quote.")
        except ValueError:
            issues.append("Validity must be an exact YYYY-MM-DD date.")
    missing = [
        key
        for key in (
            "vendor",
            "currency",
            "tax",
            "fee",
            "cancellation",
            "payment",
            "inclusions",
            "deposit",
            "overtime",
            "valid until",
        )
        if not values.get(key)
    ]
    if total is None:
        missing.append("all-in total or valid priced items")
    if not items:
        missing.append("line-item breakdown")
    importable = (
        not issues
        and currency is not None
        and total is not None
        and not any(parsed[key] is None for key in ("tax", "fee"))
    )
    return QuoteAnalysis(
        filename=body.filename,
        source_text=body.text,
        source_hash=hashlib.sha256(body.text.encode()).hexdigest(),
        currency=currency,
        vendor_name=values.get("vendor"),
        category_key=body.category_key,
        items=items,
        subtotal=subtotal,
        tax=parsed["tax"],
        fee=parsed["fee"],
        reported_total=parsed["all-in total"],
        comparable_total=total,
        deposit=parsed["deposit"],
        terms={
            key: values[key]
            for key in ("cancellation", "payment", "overtime", "valid until", "inclusions")
            if key in values
        },
        payments=payments,
        evidence=evidence,
        issues=issues,
        missing=missing,
        importable=importable,
    )
