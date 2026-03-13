from config import app

import secrets
import os

from datetime import datetime

from flask import request, render_template, redirect, url_for, session
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
        return handle_feedback_post(form)
    populate_form_for_get(form)
    return render_feedback_page(form)


@app.route(root_path + "/success")
def success(name="success"):
    return render_template("success.html", thanks=_("Thank you for your feedback!"))

@app.route(root_path + "/error")
def error(name="error"):
    # Accept error message as query parameter, fallback to default
    error_msg = request.args.get("error") or _( "There was a problem sending your message.")
    return render_template(
        "error.html", error=error_msg
    ), 400

def handle_feedback_post(form):
    """Handle POST request for feedback form."""
    form_subject = form.subject.data
    municipality_id = int(form.municipality.data)
    municipality_name = index_to_name(municipality_id)
    municipality_email = index_to_email(municipality_id)
    recipients = set_recipients(form_subject, municipality_email)
    email_subject = f"E-Kirjasto palaute - {municipality_name}: {form_subject}"
    user_agent = request.headers.get("User-Agent")
    body = build_feedback_body(form, user_agent)

    sent = send_email(email_subject, body, nh3.clean(form.email.data), recipients)
    if sent:
        return redirect(url_for("success"))
    else:
        error_msg = _("There was a problem sending your message.")
        return redirect(url_for("error", error=error_msg))

def populate_form_for_get(form):
    """Populate form fields from GET request args."""
    form.device_manufacturer.data = request.args.get("device_manufacturer")
    form.device_model.data = request.args.get("device_model")
    form.version_name.data = request.args.get("version_name")
    form.version_code.data = request.args.get("version_code")
    form.commit.data = request.args.get("commit")

def render_feedback_page(form):
    """Render feedback page for GET request."""
    languages = {
        "en": _("English"),
        "fi": _("Finnish"),
        "sv": _("Swedish"),
    }
    info_text = _(
        "You can leave feedback about the E-library or suggest materials for acquisition. Suggestions for materials will not be responded to."
    )
    privacy_policy_urls = {
        "fi": "https://www.kansalliskirjasto.fi/fi/e-kirjasto/e-kirjaston-tietosuoja-ja-rekisteriseloste",
        "sv": "https://www.kansalliskirjasto.fi/sv/e-biblioteket/dataskydds-och-registerbeskrivning",
        "en": "https://www.kansalliskirjasto.fi/en/e-library/privacy-policy-data-protection-statement-and-description-data-file",
    }
    locale = get_locale()
    policy_url = privacy_policy_urls.get(locale, privacy_policy_urls["en"])
    info_policy = _(
        "Messages sent through this feedback form will include the device's manufacturer, model, and application version to help locate errors. Our privacy policy can be found here: "
    ) + f'<a href="{policy_url}" target="_blank">{policy_url}</a>'

    return render_template(
        "feedback.html",
        form=form,
        languages=languages,
        selected_language=locale,
        info_text=info_text,
        info_policy=info_policy,
    )