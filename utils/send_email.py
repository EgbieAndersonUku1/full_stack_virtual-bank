
from django_q.tasks import async_task

from tasks.verification_tasks import send_confirmation_email


def send_confirmation_email_with_async(email: str, subject: str, verification_code: str, expiry_time: str = "10"):
    async_task(send_confirmation_email,
               email,
               subject,
               verification_code,
               expiry_time
               )