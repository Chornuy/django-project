from django.core.mail import EmailMultiAlternatives
from django.template import loader


def send_from_template_email(
    subject_template_name: str, email_template_name: str, context: dict, from_email: str, to_email: str
):
    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    html_email = loader.render_to_string(email_template_name, context)
    email_message.attach_alternative(html_email, "text/html")

    email_message.send()
