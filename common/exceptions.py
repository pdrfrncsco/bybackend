"""
BOLAYETU — Custom Exception Handler

Translates all DRF exceptions into the standard error envelope:
    {
        "success": false,
        "message": "Human-readable error",
        "errors": { field: [errors] }
    }
"""

import logging
from typing import Any

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Global exception handler for all DRF views.

    Wraps standard DRF error responses in the Bolayetu standard envelope.
    Unhandled exceptions are logged and returned as 500 errors.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "message": _extract_message(response.data),
            "errors": _extract_errors(response.data),
        }
        response.data = error_data
        return response

    # Unhandled server error
    logger.exception(
        "Unhandled exception in view",
        extra={
            "view": context.get("view"),
            "request": context.get("request"),
        },
    )

    return Response(
        {
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "errors": {},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_message(data: Any) -> str:
    """Extract the primary human-readable error message from response data."""
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        first = data[0] if data else "An error occurred."
        return str(first)

    if isinstance(data, dict):
        # Standard DRF detail key
        if "detail" in data:
            return str(data["detail"])

        # Non-field errors
        if "non_field_errors" in data:
            errors = data["non_field_errors"]
            return str(errors[0]) if errors else "Validation failed."

        # First field error
        for key, value in data.items():
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            if isinstance(value, str):
                return f"{key}: {value}"

    return "An error occurred."


def _extract_errors(data: Any) -> dict:
    """Extract field-level errors from response data."""
    if isinstance(data, dict):
        # Exclude the detail key — it's already in message
        return {k: v for k, v in data.items() if k != "detail"}

    return {}
