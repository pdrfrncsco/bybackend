"""
BOLAYETU — Organizations Exceptions

Domain-specific exceptions for the organizations module.
All exceptions are caught by the global exception handler and
translated into the standard error envelope.
"""

from rest_framework import status
from rest_framework.exceptions import APIException


class OrganizationException(APIException):
    """Base exception for all organizations domain errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An organizations error occurred."
    default_code = "organizations_error"


class OrganizationNotFound(OrganizationException):
    """Raised when an organization (tenant) does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Organization not found."
    default_code = "organization_not_found"


class OrganizationAlreadyExists(OrganizationException):
    """Raised when attempting to create a duplicate organization."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "An organization with this name or subdomain already exists."
    default_code = "organization_already_exists"


class NotOrganizationAdmin(OrganizationException):
    """Raised when a non-admin user attempts to modify an organization."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You must be an organization administrator to perform this action."
    default_code = "not_organization_admin"


class NoOrganizationMembership(OrganizationException):
    """Raised when a user has no active membership in any organization."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "You are not a member of any organization."
    default_code = "no_organization_membership"


class SubscriptionAlreadyExists(OrganizationException):
    """Raised when a user attempts to subscribe to an organization they already follow."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "You are already subscribed to this organization."
    default_code = "subscription_already_exists"


class SubscriptionNotFound(OrganizationException):
    """Raised when a user attempts to unsubscribe from an organization they don't follow."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "You are not subscribed to this organization."
    default_code = "subscription_not_found"


class InvalidLogoFile(OrganizationException):
    """Raised when an uploaded logo file is invalid (type, size)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid logo file. Please upload a valid image (JPEG, PNG, WebP, SVG) under 5MB."
    default_code = "invalid_logo_file"


class OrganizationSuspended(OrganizationException):
    """Raised when an operation is attempted on a suspended organization."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "This organization is currently suspended."
    default_code = "organization_suspended"
