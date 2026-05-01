import logging

from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender_constants import LoggerType
from django_email_sender.email_sender_constants import EmailSenderConstants
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from authentication.models import EmailLog

logger = logging.getLogger("email_sender")


def send_confirmation_email(username, email: str, subject: str, verification_code: str, expiry_time: str = "10") -> None:
    """"""
    params = {
        "username": username,
        "email": email,
        "subject": subject,
        "verification_code": verification_code,
        "expiry_time": expiry_time
    }

    for name, value in params.items():
        if not isinstance(value, str):
            raise ValueError(
                _(f"Expected {name} to be a string but got {type(value).__name__}")
            )
        
        
    email_sender_logger = EmailSenderLogger.create()

    (
        email_sender_logger
        .start_logging_session()
        .enable_verbose()
        .add_log_model(EmailLog)
        .enable_email_meta_data_save()
        .add_email_sender_instance(EmailSender())
        .config_logger(logger, LoggerType.DEBUG)
        .from_address(settings.EMAIL_HOST)
        .exclude_fields_from_logging(EmailSenderConstants.Fields.CONTEXT.value)
        .to(email)
        .with_subject(subject)
        .with_context({"verification_code": verification_code, "expiry_time": expiry_time, "username": username})
        .with_html_template("confirmation.html", folder_name="register")
        .with_text_template("confirmation.txt", folder_name="register")
        .send()
    )

    # print(email_sender_logger.return_successful_payload())
    