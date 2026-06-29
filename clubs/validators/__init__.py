"""
BOLAYETU — Clubs Validators

Reusable validation functions for the clubs domain.
"""

from django.core.exceptions import ValidationError

from clubs.constants import (
    MAX_LOGO_SIZE,
    ALLOWED_LOGO_TYPES,
    MIN_JERSEY_NUMBER,
    MAX_JERSEY_NUMBER,
    MIN_FOUNDED_YEAR,
    MAX_FOUNDED_YEAR,
)


def validate_logo_file(file) -> None:
    """
    Validate that an uploaded logo file meets requirements.

    Checks:
        - File size does not exceed MAX_LOGO_SIZE (5 MB)
        - File content type is in ALLOWED_LOGO_TYPES
    """
    if file.size > MAX_LOGO_SIZE:
        max_mb = MAX_LOGO_SIZE // (1024 * 1024)
        raise ValidationError(f"Logo file size must not exceed {max_mb}MB.")

    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_LOGO_TYPES:
        raise ValidationError("Logo must be a JPEG, PNG, WebP, or SVG image.")


def validate_jersey_number(number: int) -> None:
    """Validate that a jersey number is within the allowed range."""
    if number < MIN_JERSEY_NUMBER or number > MAX_JERSEY_NUMBER:
        raise ValidationError(
            f"Jersey number must be between {MIN_JERSEY_NUMBER} and {MAX_JERSEY_NUMBER}."
        )


def validate_founded_year(year: int) -> None:
    """Validate that a founded year is reasonable."""
    if year < MIN_FOUNDED_YEAR or year > MAX_FOUNDED_YEAR:
        raise ValidationError(
            f"Founded year must be between {MIN_FOUNDED_YEAR} and {MAX_FOUNDED_YEAR}."
        )
