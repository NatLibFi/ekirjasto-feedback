import secrets
import smtplib
import ssl
import os

from datetime import datetime

from flask import Flask, render_template, request, render_template, redirect, url_for

from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import (
    StringField,
    HiddenField,
    TextAreaField,
    EmailField,
    SelectField,
    SubmitField,
    validators,
)

from wtforms.validators import DataRequired, Length
from flask_babel import lazy_gettext as _
from flask_babel import Babel

from municipalities import indexed_municipalities, index_to_email, index_to_name

from email.message import EmailMessage
import nh3

app = Flask(__name__)

# root path of the application can be set with the ROOT_PATH environment variable
# If not set, it defaults to /
root_path = os.environ.get("ROOT_PATH", "/")

from config import app


def get_locale():
    return request.args.get("lang") or "fi"


babel = Babel(app, locale_selector=get_locale)


# Bootstrap-Flask requires this line
bootstrap = Bootstrap5(app)
# Flask-WTF requires this line
csrf = CSRFProtect(app)
app.secret_key = secrets.token_urlsafe(16)


class FeedbackForm(FlaskForm):
    subject = SelectField(
        _("Subject"),
        choices=[
            (_("General feedback")),
            (_("Material procurement")),
            (_("Material error")),
            (_("Technical problem")),
            (_("Other")),
        ],
    )
    device_manufacturer = HiddenField(_("Manufacturer"), [validators.Optional()])
    device_model = HiddenField(_("Device model"), [validators.Optional()])
    version_name = HiddenField(_("Software version name"), [validators.Optional()])
    version_code = HiddenField(_("Software version code"), [validators.Optional()])
    commit = HiddenField(_("Commit"), [validators.Optional()])
    book_name = StringField(
        _("Book name"), [validators.Optional(), validators.Length(1, 128)]
    )
    message = TextAreaField(
        _("Message"),
        [validators.DataRequired(), validators.Length(1, 2048)],
    )
    municipality = SelectField(
        _("My home municipality that receives this feedback"),
        choices=indexed_municipalities(),
        render_kw={
            "class": "form-select",
            "data-control": "select2",
            "data-dropdown-parent": "body",
        },
    )
    email = EmailField(
        _("Email address, if you want an answer to your feedback (Optional)"),
        [validators.Optional()],
    )
    submit = SubmitField(
        _("Send"),
    )


@app.route(root_path, methods=["GET", "POST"])
def feedback(name=None):
    form = FeedbackForm()

    if request.method == "POST" and form.validate():
        subject = form.subject.data
        municipality_id = int(form.municipality.data)
        municipality_name = index_to_name(municipality_id)
        municipality_email = index_to_email(municipality_id)

        subject = f"E-Kirjasto palaute - {municipality_name}: {subject}"
        recipients = [
            municipality_email,
            app.config["ALWAYS_RECIPIENT"],
        ]

        body = nh3.clean(form.message.data)
        reply_to = nh3.clean(form.email.data)
        book_name = nh3.clean(form.book_name.data)
        device_model = nh3.clean(form.device_model.data)
        device_manufacturer = nh3.clean(form.device_manufacturer.data)
        version_name = nh3.clean(form.version_name.data)
        version_code = nh3.clean(form.version_code.data)
        commit = nh3.clean(form.commit.data)
        user_agent = request.headers.get("User-Agent")

        body += f"\n\nHaluan vastauksen osoitteeseen: {reply_to}"
        body += f"\n\nKirjan nimi: {book_name}"
        body += f"\n\nLaitteen malli ja valmistaja: {device_manufacturer} {device_model}"
        body += f"\n\nOhjelmistoversio: {version_name} ({version_code}) (commit: {commit})"
        body += f"\n\nUser agent: {user_agent}"

        sent = send_email(subject, body, reply_to, recipients)

        if sent:
            return redirect(url_for("success"))
        else:
            return redirect(url_for("error"))

    # Getting these from config.py with translation didn't seem to work
    # Note that these are "translated" into the original language so every language displays "English" so you always find it
    languages = {
        "en": _("English"),
        "fi": _("Finnish"),
        "sv": _("Swedish"),
    }

    form.device_manufacturer.data = request.args.get("device_manufacturer")
    form.device_model.data = request.args.get("device_model")
    form.version_name.data = request.args.get("version_name")
    form.version_code.data = request.args.get("version_code")
    form.commit.data = request.args.get("commit")

    info_text = _("You can leave feedback about the E-library or suggest materials for acquisition. Suggestions for materials will not be responded to.")

    return render_template(
        "feedback.html",
        form=form,
        languages=languages,
        selected_language=get_locale(),
        info_text=info_text,
    )



def send_email(subject, body, reply_to, recipients):
    '''Function that sends emails to recipients.

    Args:
        subject (str): the subject field of the email message to be sent
        body (str): the text body of the email being sent
        reply_to (str): The Reply-To header value
        recipients (list): List of recipients

    Returns:
        bool: Return value is True if message was sent or False if not
    '''

    # Prevents duplicates
    recipients = list(set(recipients))
    message = EmailMessage()

    message.set_content(body)
    message["To"] = ",".join(recipients)
    message["From"] = app.config["MAIL_SENDER"]
    message["Subject"] = subject
    # Setting the Reply-To header here so that replying to emails is more convenient
    if reply_to:
        message["Reply-To"] = reply_to

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
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


def save_message(message):
    """
    If sending the email fails for any reason, this is used to save the message to disk as a backup
    """
    try:
        f = open(app.config["BACKUP_FILE"], "a", encoding="utf-8")
        f.write(message)
    except Exception as exception:
        return False
    return True


@app.route(root_path + "/success")
def success(name="success"):
    return render_template("success.html", thanks=_("Thank you for your feedback!"))


@app.route(root_path + "/error")
def error(name="error"):
    return render_template(
        "error.html", error=_("There was a problem sending your message.")
    ), 400
