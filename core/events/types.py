"""
BOLAYETU — Domain Event Type Registry

Central registry of event type name constants, following the past-tense
naming convention defined in docs/01-architecture/10_EVENTS_AND_WORKFLOWS.md (§7).

Publishers and subscribers should reference these constants instead of raw
strings, so a typo or rename is caught by search/refactor tools instead of
silently breaking the publisher → subscriber link.
"""


class EventType:
    """Known domain event type names."""

    # Media (media_assets domain) — see 08A_DIGITAL_ASSET_MANAGEMENT.md
    ASSET_UPLOADED = "AssetUploaded"

    # Clubs domain — see 10_EVENTS_AND_WORKFLOWS.md §10 and §19
    CLUB_APPROVED = "ClubApproved"
    CLUB_SUSPENDED = "ClubSuspended"


__all__ = ["EventType"]
