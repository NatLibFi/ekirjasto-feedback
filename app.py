import secrets
import re
import sys
import smtplib
import ssl
import os

from datetime import datetime

from flask import Flask
from flask import render_template
from flask import request

from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import (
    StringField,
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

from flask import Flask

from email.message import EmailMessage
import nh3

app = Flask(__name__)

# root path of the application can be set with the ROOT_PATH environment variable
# If not set, it defaults to /
root_path = os.environ.get("ROOT_PATH", "/")

bootstrap = Bootstrap5(app)
from config import app


def get_locale():
    return request.args.get("lang")


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
    message = TextAreaField(
        _("Message"), [validators.DataRequired(), validators.Length(1, 2048)]
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

        body = nh3.clean(form.message.data)
        reply_to = nh3.clean(form.email.data)

        subject = f"E-Kirjasto palaute - {municipality_name}: {subject}"
        recipients = [
            municipality_email,
            app.config["ALWAYS_RECIPIENT"],
        ]

        sent = send_email(
            subject,
            body,
            recipients,
            reply_to,
        )

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

    return render_template(
        "feedback.html",
        form=FeedbackForm(),
        languages=languages,
        selected_language=get_locale(),
    )


def send_email(subject, body, recipients, reply_to):
    if type(subject) is not str:
        raise ValueError("subject must be a string")

    if type(body) is not str:
        raise ValueError("body must be a string")

    if type(recipients) is not list:
        raise ValueError("recipients must be a list")

    # Prevents duplicates
    recipients = list(set(recipients))
    message = EmailMessage()

    if reply_to:
        body += f"\n\nHaluan vastauksen osoitteeseen: {reply_to}"

    message.set_content(body)
    message["To"] = ",".join(recipients)
    message["From"] = app.config["MAIL_SENDER"]
    message["Subject"] = f"E-Kirjasto palaute: {subject}"

    context = ssl.create_default_context()
    server = app.config["MAIL_SERVER"]
    port = app.config["MAIL_PORT"]
    sender_email = app.config["MAIL_SENDER"]
    username = app.config["MAIL_USERNAME"]
    password = app.config["MAIL_PASSWORD"]

    try:
        with smtplib.SMTP_SSL(server, port, context=context) as server:
            server.login(username, password)
            server.sendmail(sender_email, recipients, message.as_string())
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
    f = open(app.config["BACKUP_FILE"], "a", encoding="utf-8")
    f.write(message)


@app.route(root_path + "/success")
def success(name="success"):
    return render_template("success.html", thanks=_("Thank you for your feedback!"))


@app.route(root_path + "/error")
def error(name="error"):
    return render_template(
        "error.html", error=_("There was a problem sending your message.")
    ), 400
