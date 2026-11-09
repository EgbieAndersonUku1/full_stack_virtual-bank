
from django_q.tasks import async_task

from tasks.verification_tasks import send_confirmation_email, send_welcome_email
from tasks.forgotten_password_task import send_password_reset_email


def send_confirmation_email_with_async(username: str,
                                       email: str,
                                       subject: str,
                                       verification_code: str,
                                       expiry_time: str = "10"
                                       ):

    async_task(send_confirmation_email,
               username,
               email,
               subject,
               verification_code,
               expiry_time
               )



def send_welcome_email_with_async( subject : str,
                                   email: str,
                                    first_name: str,
                                    last_name: str,
                                    account_last_4: str,
                                    sort_code_masked: str,
                                    bank_name: str
                                    ):

    async_task(send_welcome_email,
             subject,
             email,
             first_name,
             last_name,
             account_last_4,
             sort_code_masked,
             bank_name
             )


def send_forgotten_password_link_with_async(subject : str,
                                            email: str,
                                            domain: str,
                                            use_https: bool,
                                           ):

     async_task(send_password_reset_email,
                 subject,
                 email,
                 domain,
                 use_https
                 )
