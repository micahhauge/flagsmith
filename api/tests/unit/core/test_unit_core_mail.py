import logging

from core.mail import safe_send_mail
from django.core.exceptions import ImproperlyConfigured


def test_safe_send_mail(mocker, settings, caplog):
    # Given
    settings.LOG_LEVEL = "INFO"
    mocker.patch("core.mail.send_mail", side_effect=ImproperlyConfigured)

    # When
    safe_send_mail(
        subject="subject",
        message="Hello!",
        from_email="noreply@example.com",
        recipient_list=["recipient@example.com"],
        html_message="<h1>Hello!</h1>",
    )

    # Then
    # exception is handled
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert (
        caplog.records[0].message
        == "Unable to send mail. Verify that EMAIL_BACKEND is set and configured correctly."
    )
