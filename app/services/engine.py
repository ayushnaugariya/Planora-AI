"""Deterministic planning engine.

Everything numeric (budget split, deadlines, health score) is computed here in
plain Python so figures are exact and reproducible. The Gemini layer only adds
personalisation (ideas, tips, narrative) on top of this verified core.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.schemas.planning import (
    AIExtras,
    BudgetLine,
    Idea,
    Milestone,
    PlanRequest,
    VendorGroup,
    Warning_,
)

# --------------------------------------------------------------------------- #
# Budget templates: (key, label, percent, tip). Each template sums to 100.
# --------------------------------------------------------------------------- #
BUDGET_TEMPLATES: dict[str, list[tuple[str, str, int, str]]] = {
    "wedding": [
        ("venue", "Venue", 20, "Off-peak dates and weekdays can cut venue cost by 15-30%."),
        ("catering", "Food and drinks", 30, "Per-plate pricing scales with guests; confirm headcount late."),
        (
            "photo_video",
            "Photography and video",
            10,
            "Book early; ask for a shot list and delivery date in writing.",
        ),
        ("attire_beauty", "Attire and beauty", 8, "Schedule fittings with buffer for alterations."),
        ("decor", "Decor and flowers", 8, "Reuse ceremony flowers at the reception."),
        ("entertainment", "Music and entertainment", 6, "A good MC matters more than a long playlist."),
        (
            "stationery",
            "Invitations and stationery",
            2,
            "Digital invites with RSVP tracking save time and money.",
        ),
        ("transport_stay", "Transport and stay", 4, "Negotiate a block rate for out-of-town guests."),
        ("favors", "Favors and gifts", 2, "Consumable favors waste less."),
        ("contingency", "Contingency", 10, "Keep this untouched until the final two weeks."),
    ],
    "birthday": [
        ("venue", "Venue", 20, "Home, park or a restaurant private room can beat a hall."),
        ("catering", "Food and drinks", 35, "Plan 1.2 servings per guest for finger food."),
        ("cake", "Cake and desserts", 6, "Order 2-3 weeks ahead and confirm allergens."),
        ("decor", "Decor and balloons", 10, "One strong backdrop beats many small props."),
        ("entertainment", "Entertainment and activities", 12, "Match activities to the age range."),
        ("photo_video", "Photography", 4, "A friend with a good phone plus a shot list works well."),
        ("stationery", "Invitations", 2, "Group chat or digital invite is enough."),
        ("favors", "Favors and return gifts", 3, "Set a per-head cap before shopping."),
        ("contingency", "Contingency", 8, "Weather, late guests, extra seating."),
    ],
    "community": [
        ("venue", "Venue and permits", 15, "Check permit lead times with the local authority first."),
        ("catering", "Food and refreshments", 28, "Water and shade matter more than variety outdoors."),
        (
            "equipment_av",
            "Sound, lighting and equipment",
            15,
            "Rent a full package and test it the day before.",
        ),
        ("marketing", "Promotion and signage", 10, "Partner with local groups to reach more people free."),
        (
            "entertainment",
            "Activities and performers",
            12,
            "Mix one headline act with several free local acts.",
        ),
        ("staffing", "Volunteers and staffing", 6, "Feed and brief volunteers; assign a clear lead each."),
        ("insurance_safety", "Insurance and safety", 6, "First aid, crowd flow and an incident plan."),
        ("contingency", "Contingency", 8, "Weather backup and last-minute rentals."),
    ],
    "anniversary": [
        ("venue", "Venue", 22, "A restaurant private room can include service and decor."),
        ("catering", "Food and drinks", 35, "Build the menu around the couple's favourites."),
        ("decor", "Decor and flowers", 10, "Photos from each decade make personal, low-cost decor."),
        ("entertainment", "Music and entertainment", 10, "Include a short slideshow or toast segment."),
        ("photo_video", "Photography", 6, "Capture family group shots early."),
        ("gifts", "Gifts and keepsakes", 7, "A shared memory book is often the most treasured gift."),
        ("stationery", "Invitations", 2, "Digital invitations with a calendar link."),
        ("contingency", "Contingency", 8, "Keep a reserve for last-minute guest changes."),
    ],
    "baby_shower": [
        ("venue", "Venue", 18, "A host's home or a cafe corner keeps costs low."),
        ("catering", "Food and drinks", 32, "Offer a non-caffeinated drink option and clear labels."),
        ("decor", "Decor and backdrop", 14, "Pick a palette; one photo wall is enough."),
        ("entertainment", "Games and activities", 8, "Two short games beat a long programme."),
        ("cake", "Cake and desserts", 8, "Order early; confirm allergens."),
        ("favors", "Favors", 8, "Seed packets or small treats work well."),
        ("photo_video", "Photography", 4, "Assign one guest as photographer."),
        ("stationery", "Invitations", 3, "Include registry link and RSVP date."),
        ("contingency", "Contingency", 5, "Keep a reserve for extras."),
    ],
}

# Synonyms so free-text priorities map onto budget categories.
PRIORITY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "food": ("catering", "cake"),
    "catering": ("catering",),
    "venue": ("venue",),
    "photography": ("photo_video",),
    "photos": ("photo_video",),
    "music": ("entertainment",),
    "entertainment": ("entertainment",),
    "games": ("entertainment",),
    "decor": ("decor",),
    "flowers": ("decor",),
    "attire": ("attire_beauty",),
    "cake": ("cake",),
    "marketing": ("marketing",),
    "safety": ("insurance_safety",),
    "gifts": ("gifts", "favors"),
    "favors": ("favors",),
    "stay": ("transport_stay",),
    "experience": ("entertainment", "decor"),
}

PRIORITY_BOOST = 1.3

# Rough minimum viable spend per guest, in INR, before formality scaling.
BASE_PER_GUEST_INR = {
    "wedding": 3400.0,
    "birthday": 1275.0,
    "community": 510.0,
    "anniversary": 2550.0,
    "baby_shower": 1530.0,
}
FX_PER_INR = {"INR": 1.0, "USD": 1 / 85.0, "EUR": 0.92 / 85.0, "GBP": 0.79 / 85.0}
FORMALITY_MULT = {"casual": 0.7, "semi_formal": 1.0, "formal": 1.4}

# --------------------------------------------------------------------------- #
# Timeline templates: (days_before_event, title, category, note)
# --------------------------------------------------------------------------- #
TIMELINES: dict[str, list[tuple[int, str, str, str]]] = {
    "wedding": [
        (270, "Set total budget and guest-list draft", "planning", "Agree who pays for what."),
        (250, "Shortlist and book venue", "venue", "Hold two dates if possible."),
        (220, "Book photographer and videographer", "photo_video", "Popular dates fill early."),
        (190, "Book caterer and schedule tastings", "catering", "Confirm dietary options."),
        (160, "Book attire and start fittings", "attire_beauty", ""),
        (140, "Book music, MC and entertainment", "entertainment", ""),
        (120, "Send save-the-dates", "stationery", ""),
        (100, "Book decor, flowers and transport", "decor", ""),
        (70, "Send formal invitations with RSVP date", "stationery", ""),
        (45, "Finalise menu and seating approach", "catering", ""),
        (30, "Confirm RSVPs and final headcount draft", "planning", ""),
        (14, "Final vendor confirmations and payments", "vendors", "Share a one-page run sheet."),
        (7, "Run-through with key family and vendors", "planning", ""),
        (2, "Pack day-of kit and assign helpers", "planning", ""),
        (0, "Event day", "event", "Delegate; enjoy it."),
    ],
    "birthday": [
        (60, "Set budget, guest list and date", "planning", ""),
        (50, "Book venue or confirm home setup", "venue", ""),
        (40, "Choose theme; order cake early", "cake", ""),
        (30, "Send invitations", "stationery", "Ask for RSVP and allergies."),
        (21, "Book entertainment and activities", "entertainment", ""),
        (14, "Order decor and favors", "decor", ""),
        (7, "Confirm RSVPs and finalise food", "catering", ""),
        (2, "Pick up cake and supplies", "planning", ""),
        (0, "Event day", "event", ""),
    ],
    "community": [
        (90, "Define goals, budget and core team", "planning", ""),
        (80, "Apply for permits and confirm venue", "venue", "Permit lead times vary."),
        (60, "Secure insurance and safety plan", "insurance_safety", ""),
        (50, "Book sound, lighting and equipment", "equipment_av", ""),
        (45, "Confirm performers and activities", "entertainment", ""),
        (35, "Launch promotion and signage", "marketing", ""),
        (28, "Recruit and assign volunteers", "staffing", ""),
        (14, "Confirm food vendors and logistics", "catering", ""),
        (7, "Volunteer briefing and site walk-through", "planning", ""),
        (1, "Set up site and test equipment", "equipment_av", ""),
        (0, "Event day", "event", ""),
    ],
    "anniversary": [
        (90, "Set budget and guest list", "planning", ""),
        (75, "Book venue", "venue", ""),
        (60, "Plan menu and book caterer", "catering", ""),
        (45, "Collect photos and stories for tribute", "planning", ""),
        (30, "Send invitations", "stationery", ""),
        (21, "Book music and photographer", "entertainment", ""),
        (10, "Confirm RSVPs and finalise seating", "planning", ""),
        (3, "Collect gifts, cake and decor", "decor", ""),
        (0, "Event day", "event", ""),
    ],
    "baby_shower": [
        (60, "Set budget, date and guest list", "planning", ""),
        (50, "Book venue or confirm host's home", "venue", ""),
        (40, "Choose theme and order invitations", "stationery", ""),
        (30, "Send invitations with registry link", "stationery", ""),
        (21, "Plan games and order cake", "cake", ""),
        (14, "Order favors and decor", "favors", ""),
        (7, "Confirm RSVPs and menu", "catering", ""),
        (2, "Set up and prep food", "planning", ""),
        (0, "Event day", "event", ""),
    ],
}

# --------------------------------------------------------------------------- #
# Vendor library, keyed by budget category key.
# (base_book_by_days, checklist, questions to ask, red flags)
# --------------------------------------------------------------------------- #
VENDOR_LIBRARY: dict[str, dict] = {
    "venue": {
        "days": 240,
        "checklist": [
            "Visit in person at the same time of day as the event",
            "Confirm capacity, layout and accessibility (ramps, restrooms)",
            "Check power, parking and sound limits",
            "Get a written contract with cancellation terms",
            "Confirm rain or heat backup",
        ],
        "ask": [
            "What is included in the price (tables, chairs, staff, cleaning)?",
            "What are the overtime and damage-deposit terms?",
            "Can outside caterers and decorators work here?",
        ],
        "red_flags": ["No written contract", "Vague 'service charges'", "Refuses a site visit"],
    },
    "catering": {
        "days": 150,
        "checklist": [
            "Attend a tasting and note portion sizes",
            "Confirm dietary and allergy handling in writing",
            "Agree final headcount deadline and per-plate price",
            "Confirm staff count, service style and cleanup",
            "Check food-safety licence",
        ],
        "ask": [
            "What is the price per plate at my guest count?",
            "How do you handle vegetarian, vegan and allergy needs?",
            "What happens if the headcount changes late?",
        ],
        "red_flags": ["No licence shown", "No tasting offered", "Price excludes staff or taxes"],
    },
    "photo_video": {
        "days": 210,
        "checklist": [
            "Review a full gallery, not just highlights",
            "Agree coverage hours and delivery date",
            "Confirm backup photographer and equipment",
            "Share a must-have shot list",
            "Clarify usage rights and album costs",
        ],
        "ask": [
            "How many edited photos will I receive and by when?",
            "What happens if you are unwell on the day?",
            "Is overtime billed hourly?",
        ],
        "red_flags": ["Only shows highlight reels", "No backup plan", "Big upfront payment, no contract"],
    },
    "attire_beauty": {
        "days": 150,
        "checklist": [
            "Schedule fittings with time for alterations",
            "Book hair and makeup trial",
            "Confirm delivery and return dates",
        ],
        "ask": ["What is the alteration timeline?", "Is there a rush fee?"],
        "red_flags": ["No written timeline", "No trial offered"],
    },
    "decor": {
        "days": 90,
        "checklist": [
            "Share a mood board and colour palette",
            "Get an itemised quote with setup and teardown",
            "Confirm what can be reused between ceremony and reception",
            "Check venue rules on flames, confetti and fixings",
        ],
        "ask": ["Who removes decor after the event?", "What substitutions if a flower is unavailable?"],
        "red_flags": ["No itemised quote", "Refuses to put substitutions in writing"],
    },
    "entertainment": {
        "days": 120,
        "checklist": [
            "Hear or watch a recent live set",
            "Share a must-play and do-not-play list",
            "Confirm equipment, power and setup time",
            "Agree a schedule with the MC or host",
        ],
        "ask": ["What is your backup if you are unavailable?", "What is your overtime rate?"],
        "red_flags": ["Won't share references", "Unclear equipment responsibilities"],
    },
    "cake": {
        "days": 30,
        "checklist": [
            "Confirm size per guest count and flavours",
            "State allergens clearly",
            "Agree pickup or delivery time",
        ],
        "ask": ["Do you deliver and set up?", "Can you label ingredients?"],
        "red_flags": ["No ingredient list", "No cancellation terms"],
    },
    "transport_stay": {
        "days": 90,
        "checklist": [
            "Negotiate a room block for out-of-town guests",
            "Arrange transfers between stay and venue",
            "Share a simple travel info sheet with guests",
        ],
        "ask": ["What is the cut-off date for the block?", "Is there a free cancellation window?"],
        "red_flags": ["No written block agreement"],
    },
    "equipment_av": {
        "days": 45,
        "checklist": [
            "Confirm sound coverage for the crowd size",
            "Check power sources and backup generator",
            "Test everything the day before",
            "Confirm setup and teardown crew",
        ],
        "ask": ["What is the maximum crowd for this package?", "Who is on call during the event?"],
        "red_flags": ["No technician on site", "No backup power"],
    },
    "insurance_safety": {
        "days": 45,
        "checklist": [
            "Get event liability insurance",
            "Prepare a first-aid point and incident log",
            "Plan crowd flow and emergency exits",
            "Share an emergency contact sheet with volunteers",
        ],
        "ask": ["What does the policy exclude?", "Is weather cancellation covered?"],
        "red_flags": ["No incident plan", "Policy excludes your activity type"],
    },
    "marketing": {
        "days": 35,
        "checklist": [
            "Create one clear poster and a short event page",
            "Post in local groups and notice boards",
            "Ask partner organisations to share",
            "Add signage and wayfinding on the day",
        ],
        "ask": ["Which local groups can co-promote?"],
        "red_flags": ["Paid promotion without a measurable goal"],
    },
    "staffing": {
        "days": 30,
        "checklist": [
            "Recruit volunteers with clear roles and shifts",
            "Run a briefing and hand out contact sheets",
            "Arrange food, water and breaks for volunteers",
        ],
        "ask": ["Who is the single point of contact on the day?"],
        "red_flags": ["No named lead per area"],
    },
}

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def lead_days(event_type: str) -> int:
    return max(d for d, *_ in TIMELINES[event_type])


def scale_days(days: int, available: int, lead: int) -> int:
    """Scale a 'days before event' offset to fit the days actually available.

    Offsets never exceed `available`, never go below 1 unless the original is 0.
    """
    if days <= 0:
        return 0
    if available >= lead:
        return min(days, available)
    scaled = round(days * available / lead)
    return min(available, max(1, scaled))


def allocate(total: int, weights: list[float]) -> list[int]:
    """Split `total` into integer parts proportional to `weights`.

    Uses the largest-remainder method so parts always sum exactly to `total`.
    """
    s = sum(weights)
    raw = [total * w / s for w in weights]
    base = [int(r) for r in raw]
    remainder = total - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:remainder]:
        base[i] += 1
    return base


def _matches_priority(key: str, label: str, priorities: list[str]) -> bool:
    for p in priorities:
        targets = PRIORITY_SYNONYMS.get(p, ())
        if key in targets or p == key or (len(p) > 3 and p in label.lower()):
            return True
    return False


def build_budget(req: PlanRequest) -> list[BudgetLine]:
    template = BUDGET_TEMPLATES[req.event_type]
    contingency_pct = next(p for k, _, p, _ in template if k == "contingency")
    flags = [
        _matches_priority(k, label, req.priorities) and k != "contingency" for k, label, _, _ in template
    ]
    weights: list[float] = []
    for (k, _, pct, _), flagged in zip(template, flags, strict=False):
        if k == "contingency":
            weights.append(float(contingency_pct))
        else:
            weights.append(pct * (PRIORITY_BOOST if flagged else 1.0))
    # Keep contingency fixed; renormalise everything else to the remainder.
    non_cont_total = sum(w for (k, *_), w in zip(template, weights, strict=False) if k != "contingency")
    target = 100 - contingency_pct
    weights = [
        float(contingency_pct) if k == "contingency" else w * target / non_cont_total
        for (k, *_), w in zip(template, weights, strict=False)
    ]
    amounts = allocate(req.budget, weights)
    lines: list[BudgetLine] = []
    for (k, label, _, tip), amt, flagged in zip(template, amounts, flags, strict=False):
        lines.append(
            BudgetLine(
                key=k,
                label=label,
                amount=amt,
                percent=round(amt * 100 / req.budget, 1),
                per_guest=round(amt / req.guest_count, 2),
                priority=flagged,
                tip=tip,
            )
        )
    return lines


def build_timeline(req: PlanRequest, today: date) -> tuple[list[Milestone], bool]:
    available = (req.event_date - today).days
    lead = lead_days(req.event_type)
    compressed = available < lead
    items: list[Milestone] = []
    for days, title, category, note in TIMELINES[req.event_type]:
        d = scale_days(days, available, lead)
        items.append(
            Milestone(
                title=title,
                due=req.event_date - timedelta(days=d),
                days_before_event=d,
                category=category,
                note=note,
            )
        )
    items.sort(key=lambda m: (-m.days_before_event,))
    return items, compressed


def build_vendors(req: PlanRequest, budget: list[BudgetLine], today: date) -> list[VendorGroup]:
    available = (req.event_date - today).days
    lead = lead_days(req.event_type)
    groups: list[VendorGroup] = []
    for line in budget:
        spec = VENDOR_LIBRARY.get(line.key)
        if not spec:
            continue
        base = min(spec["days"], lead)
        d = scale_days(base, available, lead)
        ask = list(spec["ask"])
        checklist = list(spec["checklist"])
        if line.key == "catering" and req.dietary:
            checklist.append("Confirm options for: " + ", ".join(req.dietary))
        groups.append(
            VendorGroup(
                key=line.key,
                label=line.label,
                book_by=req.event_date - timedelta(days=d),
                budget=line.amount,
                checklist=checklist,
                ask=ask,
                red_flags=list(spec["red_flags"]),
            )
        )
    groups.sort(key=lambda g: g.book_by)
    return groups


@dataclass
class Core:
    days_until: int
    per_guest: float
    health_score: int
    compressed: bool
    warnings: list[Warning_]
    budget: list[BudgetLine]
    timeline: list[Milestone]
    vendors: list[VendorGroup]


def per_guest_threshold(req: PlanRequest) -> float:
    return BASE_PER_GUEST_INR[req.event_type] * FX_PER_INR[req.currency] * FORMALITY_MULT[req.formality]


def assess(req: PlanRequest, today: date, compressed: bool, available: int) -> tuple[int, list[Warning_]]:
    warnings: list[Warning_] = []
    score = 100
    per_guest = req.budget / req.guest_count
    threshold = per_guest_threshold(req)

    if per_guest < 0.6 * threshold:
        score -= 30
        warnings.append(
            Warning_(
                level="risk",
                message="Budget per guest is well below a typical minimum for this type of event. "
                "Consider fewer guests, a simpler format, or a larger budget.",
            )
        )
    elif per_guest < threshold:
        score -= 15
        warnings.append(
            Warning_(
                level="warn",
                message="Budget per guest is on the tight side. Prioritise two or three categories "
                "and keep the contingency intact.",
            )
        )
    elif per_guest >= 2.5 * threshold:
        warnings.append(
            Warning_(
                level="info",
                message="You have comfortable room per guest. Consider upgrading your top priority.",
            )
        )

    lead = lead_days(req.event_type)
    if compressed:
        ratio = max(available, 0) / lead
        score -= round(30 * (1 - ratio))
        level = "risk" if ratio < 0.4 else "warn"
        warnings.append(
            Warning_(
                level=level,
                message=f"Only {available} days remain; a typical plan starts {lead} days out. "
                "The timeline below is compressed, so book the biggest vendors first.",
            )
        )
    if available < 7:
        score -= 10
        warnings.append(
            Warning_(
                level="risk", message="Less than a week to go. Focus on venue, food and invitations today."
            )
        )

    big = {"wedding": 300, "birthday": 100, "community": 1000, "anniversary": 150, "baby_shower": 60}
    if req.guest_count > big[req.event_type]:
        score -= 5
        warnings.append(
            Warning_(
                level="warn",
                message="Large guest count for this event type. Plan crowd flow, seating and "
                "additional staff early.",
            )
        )
    return max(0, min(100, score)), warnings


def compute(req: PlanRequest, today: date | None = None) -> Core:
    today = today or date.today()
    available = (req.event_date - today).days
    budget = build_budget(req)
    timeline, compressed = build_timeline(req, today)
    vendors = build_vendors(req, budget, today)
    score, warnings = assess(req, today, compressed, available)
    return Core(
        days_until=available,
        per_guest=round(req.budget / req.guest_count, 2),
        health_score=score,
        compressed=compressed,
        warnings=warnings,
        budget=budget,
        timeline=timeline,
        vendors=vendors,
    )


# --------------------------------------------------------------------------- #
# Offline personalisation (used when Gemini is unavailable)
# --------------------------------------------------------------------------- #
BASE_IDEAS: dict[str, list[tuple[str, str, str]]] = {
    "wedding": [
        (
            "Golden-hour ceremony",
            "Schedule the ceremony about an hour before sunset for warm, flattering light.",
            "photo",
        ),
        (
            "Interactive food stations",
            "Replace one plated course with live stations to keep guests moving and mingling.",
            "food",
        ),
        (
            "Guest story wall",
            "Invite guests to leave a note or photo; display it as a keepsake.",
            "experience",
        ),
        (
            "Welcome kit for travellers",
            "A small bag with water, a snack and a schedule for out-of-town guests.",
            "hospitality",
        ),
    ],
    "birthday": [
        ("One-hero backdrop", "Invest in one standout photo backdrop instead of many small props.", "decor"),
        ("Activity rounds", "Run two or three short, themed activities with small prizes.", "activities"),
        ("Memory table", "Display photos from each year of the guest of honour's life.", "experience"),
        ("Build-your-own food bar", "Tacos, pizza or sundaes let every guest fit their own diet.", "food"),
    ],
    "community": [
        ("Local makers corner", "Invite neighbourhood artisans for a small market zone.", "activities"),
        ("Kids and elders zones", "Separate calm and active areas so everyone feels included.", "inclusion"),
        ("Pass-the-mic stage", "Short open-mic slots for residents between headline acts.", "entertainment"),
        (
            "Zero-waste setup",
            "Reusable cups, clearly labelled bins and a volunteer green team.",
            "sustainability",
        ),
    ],
    "anniversary": [
        (
            "Then and now slideshow",
            "Pair photos from the early years with recent ones and play softly during dinner.",
            "experience",
        ),
        (
            "Letters from loved ones",
            "Collect short notes from family and friends and present them in a book.",
            "gift",
        ),
        ("Recreate the first date menu", "Rebuild a favourite early meal as a tasting course.", "food"),
        ("Toast circle", "Three short toasts from different generations.", "experience"),
    ],
    "baby_shower": [
        ("Wishes for baby", "Guests write advice or wishes on cards for a keepsake jar.", "experience"),
        ("Diaper-and-drink bar", "Guests bring diapers and enjoy a mocktail station.", "food"),
        ("Photo wall with growth props", "Simple frame and props for guests to pose with.", "decor"),
        ("Two short games", "Keep games light and quick; one active, one quiet.", "activities"),
    ],
}


def fallback_extras(req: PlanRequest, core: Core) -> AIExtras:
    ideas = [Idea(title=t, description=d, category=c) for t, d, c in BASE_IDEAS[req.event_type]]
    if req.theme:
        ideas.insert(
            0,
            Idea(
                # Reserve 18 characters for the surrounding text and quotes.
                title=f"Style it around '{req.theme[:62]}'",
                description="Pick a three-colour palette and one signature element (backdrop, table "
                "centrepiece or entry) that expresses the theme.",
                category="decor",
            ),
        )
    if req.interests:
        ideas.append(
            Idea(
                title="Make it personal",
                description=f"Weave in what the guest of honour enjoys ({req.interests[:120]}) "
                "through one activity and one menu item.",
                category="experience",
            )
        )
    if req.dietary:
        ideas.append(
            Idea(
                title="Inclusive menu",
                description="Label every dish and offer at least one satisfying main for: "
                + ", ".join(req.dietary)
                + ".",
                category="food",
            )
        )
    if core.per_guest < per_guest_threshold(req):
        ideas.append(
            Idea(
                title="Smart savings",
                description="Move to an off-peak slot, simplify the menu to one standout dish, and "
                "borrow or DIY decor.",
                category="budget",
            )
        )
    ideas = ideas[:8]

    tips = [
        "Book the venue and the biggest vendor first; everything else depends on them.",
        "Track every payment and due date in one place and keep contracts in a shared folder.",
        "Assign one trusted person to handle questions on the day so you can enjoy the event.",
    ]
    if core.compressed:
        tips.insert(0, "Your timeline is compressed: make calls today rather than sending emails.")
    if req.guest_count > 100:
        tips.append("Collect RSVPs early and chase non-responders with a personal message.")
    tips = tips[:6]

    name = req.title or req.event_type.replace("_", " ").title()
    summary = (
        f"{name} for {req.guest_count} guests on {req.event_date:%d %b %Y}, "
        f"{core.days_until} days away. Budget works out to about "
        f"{core.per_guest:,.0f} {req.currency} per guest, and plan health is "
        f"{core.health_score}/100."
    )
    return AIExtras(summary=summary, ideas=ideas, tips=tips)


# --------------------------------------------------------------------------- #
# Calendar export
# --------------------------------------------------------------------------- #


def _ics_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> list[str]:
    """Fold a content line to 75 octets as per RFC 5545."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return [line]
    out: list[str] = []
    cur = b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not out else 74
        if len(cur) + len(b) > limit:
            out.append(cur.decode("utf-8"))
            cur = b
        else:
            cur += b
    if cur:
        out.append(cur.decode("utf-8"))
    return [out[0]] + [" " + s for s in out[1:]]


def to_ics(title: str, milestones: list[Milestone], stamp: str, *, calendar_id: str | None = None) -> str:
    # A workspace retains identity across exports/date changes. Stateless exports
    # have no saved identity and receive a fresh namespace, independent of time.
    namespace = uuid5(NAMESPACE_URL, f"eventra:{calendar_id}") if calendar_id is not None else uuid4()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Eventra//Event Planner//EN",
        "CALSCALE:GREGORIAN",
    ]
    for i, m in enumerate(milestones):
        end = m.due + timedelta(days=1)
        lines += [
            "BEGIN:VEVENT",
            f"UID:eventra-{uuid5(namespace, str(i))}@eventra.local",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{m.due:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end:%Y%m%d}",
            f"SUMMARY:{_ics_escape(title + ': ' + m.title)}",
        ]
        if m.note:
            lines.append(f"DESCRIPTION:{_ics_escape(m.note)}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    folded: list[str] = []
    for ln in lines:
        folded.extend(_fold(ln))
    return "\r\n".join(folded) + "\r\n"
