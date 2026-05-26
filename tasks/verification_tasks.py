import logging

from django.utils.translation import gettext_lazy as _
from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender_constants import LoggerType
from django_email_sender.email_sender_constants import EmailSenderConstants
from django.conf import settings


from utils.utils import validate_params_are_strings


from authentication.models import EmailLog

logger = logging.getLogger("email_sender")


def send_confirmation_email(username,
                             email: str, 
                             subject: str, 
                             verification_code: str, 
                             expiry_time: str = "10") -> None:
    """"""
    params = {
        "username": username,
        "email": email,
        "subject": subject,
        "verification_code": verification_code,
        "expiry_time": expiry_time
    }

    validate_params_are_strings(params)
   
    # pop the email and subject so the remaining fields match
    # the fields in the email and then use it in context
    params.pop("email")
    params.pop("subject")

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
        .with_context(params)
        .with_html_template("confirmation.html", folder_name="register")
        .with_text_template("confirmation.txt", folder_name="register")
        .send()
    )

   



def send_welcome_email( subject:str,
                        email:str,
                        first_name: str, 
                        last_name: str, 
                        account_last_4: str, 
                        sort_code_masked: str,
                        bank_name: str,
                        ) -> None:
    """"""
    params = {
      "first_name": first_name,
      "last_name": last_name,
      "full_name": f"{first_name} {last_name}",
      "account_last_4": account_last_4,
      "sort_code_masked": sort_code_masked,
      "bank_name": bank_name,
      "subject": subject,
      "email": email,
    }

    validate_params_are_strings(params)
        
    email_sender_logger = EmailSenderLogger.create()


    # pop the email and subject so the remaining fields match
    # the fields in the email and then use it in context
    params.pop("subject")
    params.pop("email")

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
        .with_context(params)
        .with_html_template("welcome.html", folder_name="welcome")
        .with_text_template("welcome.txt", folder_name="welcome")
        .send()
    )

  
    