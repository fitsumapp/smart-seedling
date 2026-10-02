"""Custom DRF Exception Handler for standard, production-safe JSON error responses."""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Standardizes error responses into a consistent JSON envelope:
    {
      "success": false,
      "error": "Error description or dictionary of field errors",
      "code": "status_code_or_identifier"
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_detail = response.data
        if isinstance(error_detail, dict) and 'detail' in error_detail:
            error_detail = error_detail['detail']

        custom_data = {
            'success': False,
            'error': error_detail,
            'status_code': response.status_code
        }
        response.data = custom_data
        return response

    # Unhandled 500 error: log securely and return clean message
    logger.error("Unhandled API Exception: %s", exc, exc_info=True)
    return Response(
        {
            'success': False,
            'error': 'An internal server error occurred while processing the request.',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
