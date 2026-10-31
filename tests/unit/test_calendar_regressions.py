"""Calendar identity must not depend on an export clock or title."""

from app.services import engine
from tests.conftest import make_req


def identifiers(text):
    return {line for line in text.splitlines() if line.startswith("UID:")}


def test_saved_calendar_identity_survives_title_and_export_time_changes():
    timeline = engine.compute(make_req()).timeline
    first = engine.to_ics("Original", timeline, "20260101T000000Z", calendar_id="workspace-one")
    later = engine.to_ics("Renamed", timeline, "20260102T000000Z", calendar_id="workspace-one")
    other = engine.to_ics("Original", timeline, "20260101T000000Z", calendar_id="workspace-two")
    assert identifiers(first) == identifiers(later)
    assert identifiers(first).isdisjoint(identifiers(other))


def test_stateless_calendars_are_distinct_even_with_identical_inputs_and_clock():
    timeline = engine.compute(make_req()).timeline
    first = engine.to_ics("Party", timeline, "20260101T000000Z")
    other = engine.to_ics("Party", timeline, "20260101T000000Z")
    assert len(identifiers(first)) == len(timeline)
    assert identifiers(first).isdisjoint(identifiers(other))
