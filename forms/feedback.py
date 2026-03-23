from wtforms import (
    StringField,
    HiddenField,
    TextAreaField,
    EmailField,
    SelectField,
    SubmitField,
    validators,
    ValidationError
)
from flask_wtf import FlaskForm

from flask_babel import lazy_gettext as _
from municipalities import indexed_municipalities

def validate_municipality(form, field):
    if field.data == "":
        raise ValidationError(_("Please select a valid municipality."))

class FeedbackForm(FlaskForm):
    subject = SelectField(
        _("Subject"),
        choices=[
            (_( "General feedback")),
            (_( "Suggest a new book or magazine")),
            (_( "Report a technical problem")),
            (_( "Other feedback")),
        ],
        description=_("Select the subject of your feedback. Please note that if you make" \
        " a suggestion about the same book or magazine from the same device, it will not be" \
        " handled."),
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
        choices=[("", _("Select a municipality"))] + indexed_municipalities(),
        render_kw={
            "class": "form-select",
            "data-control": "select2",
            "data-dropdown-parent": "body",
        },
        validators=[validators.DataRequired(), validate_municipality],
        description=_("Your home municipality is needed to direct your feedback to the right" \
        " library."),
    )
    email = EmailField(
        _("Email address, if you want an answer to your feedback (Optional)"),
        [validators.Optional()],
    )
    submit = SubmitField(
        _("Send"),
    )