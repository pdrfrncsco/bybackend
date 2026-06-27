"""
BOLAYETU — Custom Exception Handler
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats errors consistently.
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize error response format
        error_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_error_message(response.data),
                'details': response.data if isinstance(response.data, dict) else None
            }
        }
        response.data = error_data
    
    return response


def get_error_message(data):
    """Extract human-readable error message"""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return data[0] if data else 'An error occurred'
    if isinstance(data, dict):
        if 'detail' in data:
            return data['detail']
        if 'message' in data:
            return data['message']
        # Get first error from field errors
        for key, value in data.items():
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            if isinstance(value, str):
                return f"{key}: {value}"
    return 'An error occurred'
