"""Public projection is explicit; saved private event objects are never serialized publicly."""

import hashlib
from zoneinfo import ZoneInfo

from app.schemas.websites import PublicRSVP, PublicVenue, PublicWebsite, ScheduleItem, WebsiteConfig


def defaults(base, preferred=None, day=None):
    theme = {"wedding": "ethereal", "birthday": "celebration", "anniversary": "editorial_luxe"}.get(
        base.details.event_type, "modern_minimal"
    )
    accent = preferred.concept.palette[0] if preferred and preferred.concept.palette else "#7863b4"
    zone = day.timezone if day and not day.timezone.startswith("server-") else "UTC"
    event_tasks = {t.id for t in base.tasks if base.plan.timeline[t.milestone_index].category == "event"}
    start = (
        next((t.planned_start for t in day.tasks if t.id in event_tasks and t.planned_start), None)
        if day
        else None
    )
    if start and start.astimezone(ZoneInfo(zone)).date() != base.details.event_date:
        start = None  # An unrelated operational time must not become an invented event start.
    return WebsiteConfig(
        event_type=base.details.event_type,
        title=base.plan.title,
        event_date=base.details.event_date,
        theme=theme,
        accent=accent,
        city=base.details.city,
        timezone=zone,
        start_at=start,
        invitation=f"Join us for {base.plan.title} on {base.details.event_date.isoformat()}. "
        "We would love to share this occasion with you.",
        schedule=[
            ScheduleItem(title=m.title, date=m.due) for m in base.plan.timeline if m.category == "event"
        ],
    )


def project(config, edition="preview"):
    """Hidden values are absent/null, including in the network response and page source."""
    return PublicWebsite(
        edition=edition,
        theme=config.theme,
        accent=config.accent,
        event_type=config.event_type,
        title=config.title,
        subtitle=config.subtitle,
        event_date=config.event_date,
        start_at=config.start_at,
        timezone=config.timezone,
        welcome=config.welcome,
        invitation=config.invitation,
        description=config.description,
        hosts=config.hosts if config.show_hosts else None,
        venue=PublicVenue(name=config.venue_name, address=config.venue_address, city=config.city)
        if config.show_venue
        else None,
        dress_code=config.dress_code if config.show_dress_code else None,
        schedule=config.schedule if config.show_schedule else [],
        cover=config.cover,
        gallery=config.gallery if config.show_gallery else [],
        rsvp=PublicRSVP(
            enabled=config.rsvp_enabled,
            email_required=config.rsvp_email_required,
            max_attendees=config.max_attendees,
            instructions=config.rsvp_instructions if config.rsvp_enabled else "",
        ),
    )


def preview_hash(config):
    return hashlib.sha256(project(config).model_dump_json().encode()).hexdigest()
