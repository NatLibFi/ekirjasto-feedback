import nh3
from email.message import EmailMessage
from config import app
from datetime import datetime
import smtplib
from flask_babel import lazy_gettext as _


def set_recipients(subject, municipality_email):
    """Return recipient list based on subject."""
    always_recipient = app.config["ALWAYS_RECIPIENT"]
    if subject == _("Suggest a new book or magazine"):
        return [always_recipient]
    return [municipality_email, always_recipient]

def build_feedback_body(form, user_agent):
    """Build the email body from form data and user agent."""
    body = nh3.clean(form.message.data)
    reply_to = nh3.clean(form.email.data)
    book_name = nh3.clean(form.book_name.data)
    device_model = nh3.clean(form.device_model.data)
    device_manufacturer = nh3.clean(form.device_manufacturer.data)
    version_name = nh3.clean(form.version_name.data)
    version_code = nh3.clean(form.version_code.data)
    commit = nh3.clean(form.commit.data)

    body += f"\n\nHaluan vastauksen osoitteeseen: {reply_to}"
    body += f"\n\nKirjan nimi: {book_name}"
    body += f"\n\nLaitteen malli ja valmistaja: {device_manufacturer} {device_model}"
    body += f"\n\nOhjelmistoversio: {version_name} ({version_code}) (commit: {commit})"
    body += f"\n\nUser agent: {user_agent}"
    return body

def save_message(message):
    """
    If sending the email fails for any reason, this is used to save the message to disk as a backup
    """
    try:
        f = open(app.config["BACKUP_FILE"], "a", encoding="utf-8")
        f.write(message)
    except Exception as exception:
        print(exception)
        return False
    return True

def send_email(subject, body, reply_to, recipients):
    """Function that sends emails to recipients.

    Args:
        subject (str): the subject field of the email message to be sent
        body (str): the text body of the email being sent
        reply_to (str): The Reply-To header value
        recipients (list): List of recipients

    Returns:
        bool: Return value is True if message was sent or False if not
    """

    # Prevents duplicates
    recipients = list(set(recipients))
    message = EmailMessage()

    message.set_content(body)
    message["To"] = ",".join(recipients)
    message["From"] = app.config["MAIL_FROM"]
    message["Sender"] = app.config["MAIL_SENDER"]
    message["Subject"] = subject
    # Setting the Reply-To header here so that replying to emails is more convenient
    if reply_to:
        message["Reply-To"] = reply_to

    server = app.config["MAIL_SERVER"]
    port = app.config["MAIL_PORT"]
    sender_email = app.config["MAIL_SENDER"]

    try:
        with smtplib.SMTP(server, port) as server:
            server.sendmail(sender_email, recipients, message.as_string())
            server.close()
    except Exception as exception:
        time = datetime.now()
        save_message(
            f"exception: {exception}\n{time}\nTO: {recipients}\n{subject}\n{body}\n\n"
        )
        return False
    return True
