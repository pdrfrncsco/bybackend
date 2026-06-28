"""
BOLAYETU — Standardized API Responses

All API endpoints must use these helpers to ensure
a consistent response envelope across the platform.

Success format:
    {
        "success": true,
        "message": "...",
        "data": {}
    }

Error format:
    {
        "success": false,
        "message": "...",
        "errors": {}
    }
"""

from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success_response(
    data: Any = None,
    message: str = "",
    status_code: int = status.HTTP_200_OK,
) -> Response:
    """
    Return a standardized success response.

    Args:
        data: The response payload.
        message: Human-readable description of the result.
        status_code: HTTP status code (default 200).

    Returns:
        DRF Response with success envelope.
    """
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status_code,
    )


def created_response(
    data: Any = None,
    message: str = "Resource created successfully.",
) -> Response:
    """Return a standardized 201 Created response."""
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
    )


def no_content_response() -> Response:
    """Return a standardized 204 No Content response."""
    return Response(status=status.HTTP_204_NO_CONTENT)


def error_response(
    message: str = "An error occurred.",
    errors: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Return a standardized error response.

    Args:
        message: Human-readable error message.
        errors: Detailed field-level errors.
        status_code: HTTP status code (default 400).

    Returns:
        DRF Response with error envelope.
    """
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors if errors is not None else {},
        },
        status=status_code,
    )


def unauthorized_response(message: str = "Authentication required.") -> Response:
    """Return a standardized 401 Unauthorized response."""
    return error_response(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message: str = "You do not have permission to perform this action.") -> Response:
    """Return a standardized 403 Forbidden response."""
    return error_response(message=message, status_code=status.HTTP_403_FORBIDDEN)


def not_found_response(message: str = "Resource not found.") -> Response:
    """Return a standardized 404 Not Found response."""
    return error_response(message=message, status_code=status.HTTP_404_NOT_FOUND)
