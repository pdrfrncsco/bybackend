"""
BOLAYETU — Organizations Validators

Reusable validation functions for the organizations domain.
"""

from django.core.exceptions import ValidationError

from organizations.constants import ALLOWED_LOGO_TYPES, MAX_LOGO_SIZE


def validate_logo_file(file) -> None:
    """
    Validate that an uploaded logo file meets requirements.

    Checks:
        - File size does not exceed MAX_LOGO_SIZE (5 MB)
        - File content type is in ALLOWED_LOGO_TYPES

    Args:
        file: The uploaded Django file object.

    Raises:
        ValidationError: If the file is too large or has an invalid type.
    """
    if file.size > MAX_LOGO_SIZE:
        max_mb = MAX_LOGO_SIZE // (1024 * 1024)
        raise ValidationError(
            f"Logo file size must not exceed {max_mb}MB."
        )

    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_LOGO_TYPES:
        raise ValidationError(
            "Logo must be a JPEG, PNG, WebP, or SVG image."
        )


def validate_subdomain_format(subdomain: str) -> None:
    """
    Validate that a subdomain is in a valid format.

    Rules:
        - 3 to 63 characters
        - Only lowercase letters, digits, and hyphens
        - Cannot start or end with a hyphen

    Args:
        subdomain: The subdomain string to validate.

    Raises:
        ValidationError: If the subdomain format is invalid.
    """
    import re

    if len(subdomain) < 3:
        raise ValidationError("Subdomain must be at least 3 characters long.")

    if len(subdomain) > 63:
        raise ValidationError("Subdomain must not exceed 63 characters.")

    if not re.match(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$", subdomain):
        raise ValidationError(
            "Subdomain may only contain lowercase letters, digits, and hyphens, "
            "and cannot start or end with a hyphen."
        )
