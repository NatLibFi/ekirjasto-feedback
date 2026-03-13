from config import app

import secrets
import os

from datetime import datetime

from flask import request, render_template, redirect, url_for

from flask_bootstrap import Bootstrap5
from flask_wtf import CSRFProtect
from flask_babel import lazy_gettext as _
from flask_babel import Babel

from municipalities import index_to_email, index_to_name
from utils.email_utils import set_recipients, build_feedback_body, send_email
from forms.feedback import FeedbackForm

import nh3

# root path of the application can be set with the ROOT_PATH environment variable
# If not set, it defaults to /
root_path = os.environ.get("ROOT_PATH", "/")


def get_locale():
    return request.args.get("lang") or "fi"


babel = Babel(app, locale_selector=get_locale)


# Bootstrap-Flask requires this line
bootstrap = Bootstrap5(app)
# Flask-WTF requires this line
csrf = CSRFProtect(app)
app.secret_key = secrets.token_urlsafe(16)

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
        body += (
            f"\n\nLaitteen malli ja valmistaja: {device_manufacturer} {device_model}"
        )
        body += (
            f"\n\nOhjelmistoversio: {version_name} ({version_code}) (commit: {commit})"
        )
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

    info_text = _(
        "You can leave feedback about the E-library or suggest materials for acquisition. Suggestions for materials will not be responded to."
    )

    return render_template(
        "feedback.html",
        form=form,
        languages=languages,
        selected_language=get_locale(),
        info_text=info_text,
    )



@app.route(root_path + "/success")
def success(name="success"):
    return render_template("success.html", thanks=_("Thank you for your feedback!"))


@app.route(root_path + "/error")
def error(name="error"):
    return render_template(
        "error.html", error=_("There was a problem sending your message.")
    ), 400
