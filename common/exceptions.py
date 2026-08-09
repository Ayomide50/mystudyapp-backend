from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'success': False,
            'status_code': response.status_code,
            'errors': response.data,
            'message': _extract_message(response.data)
        }
        response.data = custom_data
    else:
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        response = Response(
            {
                'success': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'An internal server error occurred. Please try again later.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response

def _extract_message(data):
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        first_key = next(iter(data), None)
        if first_key:
            val = data[first_key]
            if isinstance(val, list) and len(val) > 0:
                return f"{first_key}: {val[0]}"
            return f"{first_key}: {val}"
    elif isinstance(data, list) and len(data) > 0:
        return str(data[0])
    return 'An error occurred during processing.'
