import logging

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def safe_send_mail(*args, **kwargs):
    """
    Prevents exceptions being raised when sending emails fails on getting a connection (e.g. when using
    SendgridBackend without the SENDGRID_API_KEY setting).

    Since we use SendgridBackend as the default, we should handle this and just log an error instead.
    """

    try:
        send_mail(*args, **kwargs)
    except ImproperlyConfigured:
        logger.error(
            "Unable to send mail. Verify that EMAIL_BACKEND is set and configured correctly."
        )
