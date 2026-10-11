import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response
    # DRF didn't recognize this exception (not a validation/auth/permission/
    # not-found error), so it would otherwise bubble up into Django's HTML
    # error page -- breaking the "every response is JSON" contract the rest
    # of the API follows. Log it and return the same {"detail": ...} shape
    # as every other error response instead.
    logger.exception('Unhandled exception in API view', exc_info=exc)
    return Response({'detail': 'Internal server error.'}, status=500)
