from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.services import engine
from tests.conftest import make_req

TYPES = ["wedding", "birthday", "community", "anniversary", "baby_shower"]


@pytest.mark.parametrize("etype", TYPES)
def test_templates_sum_to_100(etype):
    assert sum(p for _, _, p, _ in engine.BUDGET_TEMPLATES[etype]) == 100


@pytest.mark.parametrize("etype", TYPES)
@pytest.mark.parametrize("budget", [1000, 12345, 999_999, 50_000_001])
def test_budget_sums_exactly(etype, budget):
    req = make_req(event_type=etype, budget=budget, guest_count=50)
    lines = engine.build_budget(req)
    assert sum(l.amount for l in lines) == budget
    assert all(l.amount >= 0 for l in lines)


def test_contingency_fixed_even_with_priorities():
    plain = engine.build_budget(make_req())
    boosted = engine.build_budget(make_req(priorities=["food", "photography"]))
    c1 = next(l for l in plain if l.key == "contingency").percent
    c2 = next(l for l in boosted if l.key == "contingency").percent
    assert abs(c1 - c2) < 0.2


def test_priority_boosts_that_category():
    plain = {l.key: l.amount for l in engine.build_budget(make_req())}
    boosted = {l.key: l.amount for l in engine.build_budget(make_req(priorities=["photography"]))}
    assert boosted["photo_video"] > plain["photo_video"]
    assert boosted["venue"] < plain["venue"]


def test_priority_flagged():
    lines = engine.build_budget(make_req(priorities=["music"]))
    assert next(l for l in lines if l.key == "entertainment").priority
    assert not next(l for l in lines if l.key == "venue").priority


def test_allocate_largest_remainder():
    assert sum(engine.allocate(101, [1, 1, 1])) == 101
    assert engine.allocate(0, [1, 2]) == [0, 0]


def test_timeline_uncompressed_uses_template_offsets():
    req = make_req(event_date=date.today() + timedelta(days=400))
    items, compressed = engine.build_timeline(req, date.today())
    assert not compressed
    assert items[0].days_before_event == 270
    assert items[-1].days_before_event == 0
    assert items[-1].due == req.event_date


def test_timeline_compressed_stays_in_future_and_ordered():
    req = make_req(event_date=date.today() + timedelta(days=30))
    items, compressed = engine.build_timeline(req, date.today())
    assert compressed
    assert all(m.due >= date.today() for m in items)
    assert all(m.due <= req.event_date for m in items)
    days = [m.days_before_event for m in items]
    assert days == sorted(days, reverse=True)


def test_event_today_everything_due_today():
    req = make_req(event_date=date.today())
    items, compressed = engine.build_timeline(req, date.today())
    assert compressed
    assert all(m.due == date.today() for m in items)


@pytest.mark.parametrize("etype", TYPES)
def test_vendor_groups_have_content_and_sorted(etype):
    req = make_req(event_type=etype, event_date=date.today() + timedelta(days=200))
    core = engine.compute(req)
    assert core.vendors
    assert [v.book_by for v in core.vendors] == sorted(v.book_by for v in core.vendors)
    for v in core.vendors:
        assert v.checklist and v.ask and v.red_flags
        assert v.book_by >= date.today()


def test_vendor_budget_matches_budget_line():
    core = engine.compute(make_req())
    by_key = {l.key: l.amount for l in core.budget}
    for v in core.vendors:
        assert v.budget == by_key[v.key]


def test_dietary_added_to_catering_checklist():
    core = engine.compute(make_req(dietary=["vegan", "gluten free"]))
    catering = next(v for v in core.vendors if v.key == "catering")
    assert any("vegan" in c for c in catering.checklist)


def test_health_score_drops_for_tight_budget_and_short_notice():
    healthy = engine.compute(
        make_req(budget=5_000_000, guest_count=100, event_date=date.today() + timedelta(days=300))
    )
    tight = engine.compute(
        make_req(budget=60_000, guest_count=400, event_date=date.today() + timedelta(days=10))
    )
    assert healthy.health_score > tight.health_score
    assert 0 <= tight.health_score <= 100
    assert any(w.level == "risk" for w in tight.warnings)


def test_comfortable_budget_gets_info_not_warning():
    core = engine.compute(make_req(budget=50_000_000, guest_count=100))
    assert any(w.level == "info" for w in core.warnings)
    assert not any(w.level in ("warn", "risk") for w in core.warnings)


def test_fallback_extras_personalised():
    req = make_req(
        event_type="birthday",
        theme="Jurassic",
        interests="dinosaurs",
        dietary=["vegetarian"],
        event_date=date.today() + timedelta(days=40),
    )
    extras = engine.fallback_extras(req, engine.compute(req))
    titles = " ".join(i.title for i in extras.ideas)
    assert "Jurassic" in titles
    assert any("vegetarian" in i.description for i in extras.ideas)
    assert 3 <= len(extras.ideas) <= 8
    assert extras.tips and extras.summary


@pytest.mark.parametrize("etype", TYPES)
@pytest.mark.parametrize("character", ["x", "\U0001f33b"], ids=["ascii", "unicode"])
@pytest.mark.parametrize("length", [62, 63, 80], ids=["exact-fit", "first-overrun", "maximum"])
def test_fallback_theme_title_stays_within_schema(etype, character, length):
    theme = character * length
    req = make_req(event_type=etype, theme=theme)
    extras = engine.fallback_extras(req, engine.compute(req))

    assert req.theme == theme
    assert all(len(idea.title) <= 80 for idea in extras.ideas)
    assert extras.ideas[0].title.startswith("Style it around '")
    assert extras.ideas[0].title.endswith("'")
    assert character * 62 in extras.ideas[0].title
    assert extras.summary and extras.tips


@pytest.mark.parametrize("theme", ["", "Jurassic"], ids=["empty", "short"])
def test_fallback_preserves_existing_theme_behavior(theme):
    req = make_req(theme=theme)
    extras = engine.fallback_extras(req, engine.compute(req))

    if theme:
        assert extras.ideas[0].title == "Style it around 'Jurassic'"
    else:
        assert [(idea.title, idea.description, idea.category) for idea in extras.ideas] == (
            engine.BASE_IDEAS[req.event_type]
        )


def test_ics_valid_structure():
    req = make_req()
    core = engine.compute(req)
    ics = engine.to_ics("Asha, Ravi; wedding", core.timeline, "20260101T000000Z")
    assert ics.startswith("BEGIN:VCALENDAR\r\n")
    assert ics.endswith("END:VCALENDAR\r\n")
    assert ics.count("BEGIN:VEVENT") == len(core.timeline) == ics.count("END:VEVENT")
    assert "Asha\\, Ravi\\; wedding" in ics
    for line in ics.split("\r\n"):
        assert len(line.encode()) <= 75


def test_ics_folds_long_lines():
    folded = engine._fold("SUMMARY:" + "x" * 200)
    assert len(folded) > 1
    assert all(len(l.encode()) <= 75 for l in folded)
    assert "".join([folded[0]] + [l[1:] for l in folded[1:]]) == "SUMMARY:" + "x" * 200


# --- validation ---------------------------------------------------------- #


def test_past_date_rejected():
    with pytest.raises(ValidationError):
        make_req(event_date=date.today() - timedelta(days=1))


def test_far_future_rejected():
    with pytest.raises(ValidationError):
        make_req(event_date=date.today() + timedelta(days=365 * 4))


@pytest.mark.parametrize(
    "field,value",
    [
        ("guest_count", 1),
        ("guest_count", 5001),
        ("budget", 10),
        ("event_type", "funeral"),
        ("currency", "JPY"),
    ],
)
def test_bounds_rejected(field, value):
    with pytest.raises(ValidationError):
        make_req(**{field: value})


def test_text_is_cleaned():
    req = make_req(notes="hello\x00\x07   world", priorities=["Food", "food", " MUSIC "])
    assert req.notes == "hello world"
    assert req.priorities == ["food", "music"]
