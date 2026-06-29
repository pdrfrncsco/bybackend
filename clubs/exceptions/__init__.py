"""
BOLAYETU — Clubs Exceptions

Domain-specific exceptions for the clubs module.
All exceptions are caught by the global exception handler and
translated into the standard error envelope.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class ClubException(APIException):
    """Base exception for all clubs domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A clubs error occurred."
    default_code = "clubs_error"


class ClubNotFound(ClubException):
    """Raised when a club does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Club not found."
    default_code = "club_not_found"


class DuplicateClubName(ClubException):
    """Raised when attempting to create a club with a name that already exists in the tenant."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "A club with this name already exists in this organization."
    default_code = "duplicate_club_name"


class NotClubAdmin(ClubException):
    """Raised when a non-admin user attempts to modify a club."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You must be a club administrator to perform this action."
    default_code = "not_club_admin"


class NoClubMembership(ClubException):
    """Raised when a user has no membership in any club."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "You are not a member of any club."
    default_code = "no_club_membership"


class ClubSuspended(ClubException):
    """Raised when an operation is attempted on a suspended club."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This club is currently suspended."
    default_code = "club_suspended"


class InvalidLogoFile(ClubException):
    """Raised when an uploaded logo file is invalid (type, size)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid logo file. Please upload a valid image (JPEG, PNG, WebP, SVG) under 5MB."
    default_code = "invalid_logo_file"


class ClubMemberNotFound(ClubException):
    """Raised when a club member does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Club member not found."
    default_code = "club_member_not_found"


class DuplicateJerseyNumber(ClubException):
    """Raised when a jersey number is already in use by another active player."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This jersey number is already in use by another active player."
    default_code = "duplicate_jersey_number"


class DuplicateClubMember(ClubException):
    """Raised when a user is already an active member of a club."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This user is already an active member of this club."
    default_code = "duplicate_club_member"
