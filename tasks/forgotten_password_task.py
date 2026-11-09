import logging
from uuid import uuid4
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django_email_sender.email_sender import EmailSender
from django_email_sender.email_logger import EmailSenderLogger
from django_email_sender.email_sender_constants import LoggerType
from django_email_sender.email_sender_constants import EmailSenderConstants
from human_seconds.converter import SecondsToTime

from authentication.models import User
from utils.utils import validate_params_are_strings
from authentication.models import EmailLog, Verification



logger = logging.getLogger("email_sender")



def send_password_reset_email(subject: str, email: str, domain: str, use_https: bool) -> None:
    """"""
    pass
