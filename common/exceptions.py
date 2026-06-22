"""
BOLAYETU — Custom Exception Handler
Normalises all API errors into a consistent envelope format.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

logger = logging.getLogger('bolayetu')


def bolayetu_exception_handler(exc, context):
    """
    Custom exception handler that normalises errors into a consistent format.

    All API error responses follow this structure:
    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Human-readable description",
            "detail": { ... }  # optional field-level detail
        }
    }
    """
    # Let DRF handle it first
    response = exception_handler(exc, context)

    if response is not None:
        error_code = _get_error_code(exc)
        error_message = _get_error_message(exc, response)
        detail = response.data if response.data != {'detail': error_message} else None

        response.data = {
            'error': {
                'code': error_code,
                'message': error_message,
                'detail': detail,
            }
        }

        # Log 5xx errors
        if response.status_code >= 500:
            logger.error(
                'API error code=%s message=%s path=%s',
                error_code,
                error_message,
                context.get('request', {}).path if hasattr(context.get('request', {}), 'path') else '',
                exc_info=True,
            )

    return response


def _get_error_code(exc) -> str:
    if isinstance(exc, ValidationError):
        return 'VALIDATION_ERROR'
    if isinstance(exc, PermissionDenied):
        return 'PERMISSION_DENIED'
    if isinstance(exc, ObjectDoesNotExist):
        return 'NOT_FOUND'
    if hasattr(exc, 'default_code'):
        return exc.default_code.upper()
    return 'ERROR'


def _get_error_message(exc, response) -> str:
    if hasattr(exc, 'detail'):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict) and 'detail' in detail:
            return str(detail['detail'])
        if isinstance(detail, list) and detail:
            return str(detail[0])
    return 'An unexpected error occurred.'


# ===================================================================
# DOMAIN EXCEPTIONS
# ===================================================================

class BolayetuException(APIException):
    """Base exception for all Bolayetu domain errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A domain error occurred.'
    default_code = 'DOMAIN_ERROR'


class TenantNotFoundException(BolayetuException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Tenant not found.'
    default_code = 'TENANT_NOT_FOUND'


class TenantAccessDeniedException(BolayetuException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have access to this tenant.'
    default_code = 'TENANT_ACCESS_DENIED'


class ResourceNotFoundException(BolayetuException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'The requested resource was not found.'
    default_code = 'RESOURCE_NOT_FOUND'


class OwnershipViolationException(BolayetuException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not own this resource.'
    default_code = 'OWNERSHIP_VIOLATION'


class SubscriptionRequiredException(BolayetuException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'This feature requires an active subscription.'
    default_code = 'SUBSCRIPTION_REQUIRED'


class InvalidOperationException(BolayetuException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'This operation is not valid.'
    default_code = 'INVALID_OPERATION'
