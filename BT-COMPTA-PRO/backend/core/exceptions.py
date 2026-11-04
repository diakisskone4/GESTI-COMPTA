from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        messages = exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages}
        return Response(messages, status=status.HTTP_400_BAD_REQUEST)
    return exception_handler(exc, context)
