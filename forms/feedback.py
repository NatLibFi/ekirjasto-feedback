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

def validate_book_name(form, field):
    if form.feedback_target.data == "books" and not (field.data or "").strip():
        raise ValidationError(_("Please enter the book name."))

def validate_book_format(form, field):
    if form.feedback_target.data == "books" and not field.data:
        raise ValidationError(_("Please select the book format."))

def is_acquisition_suggestion(form):
    return form.subject.data == str(_("Suggest a new book or magazine"))

def validate_feedback_target(form, field):
    if not is_acquisition_suggestion(form) and not field.data:
        raise ValidationError(_("Please select what your feedback concerns."))

def validate_acquisition_type(form, field):
    if is_acquisition_suggestion(form) and not field.data:
        raise ValidationError(_("Please select an acquisition suggestion type."))

class FeedbackForm(FlaskForm):
    subject = SelectField(
        _("Subject"),
        choices=[
            (_( "General feedback")),
            (_( "Suggest a new book or magazine")),
            (_( "Report a technical problem")),
        ],
        description=_("Select the subject of your feedback. Please note that if you make" \
        " a suggestion about the same book or magazine from the same device, it will not be" \
        " handled."),
    )
    feedback_target = SelectField(
        _("What does your feedback concern?"),
        choices=[
            ("", _("Select what your feedback concerns")),
            ("android", _("Android app")),
            ("ios", _("iOS app")),
            ("web", _("Web interface")),
            ("books", _("Books and audiobooks")),
            ("magazines", _("Magazines")),
            ("login", _("Login")),
            ("other", _("Other")),
        ],
        validators=[validate_feedback_target],
        render_kw={"data-conditional-required": "true"},
    )
    acquisition_type = SelectField(
        _("Which type of material are you suggesting?"),
        choices=[
            ("", _("Select an item type")),
            ("book", _("A book")),
            ("audiobook", _("An audiobook")),
            ("either", _("Either")),
            ("magazine", _("A magazine")),
        ],
        validators=[validate_acquisition_type],
        render_kw={"data-conditional-required": "true"},
    )
    device_manufacturer = HiddenField(_("Manufacturer"), [validators.Optional()])
    device_model = HiddenField(_("Device model"), [validators.Optional()])
    version_name = HiddenField(_("Software version name"), [validators.Optional()])
    version_code = HiddenField(_("Software version code"), [validators.Optional()])
    commit = HiddenField(_("Commit"), [validators.Optional()])
    book_name = StringField(
        _("Book or magazine name"),
        [validators.Length(max=128), validate_book_name],
        render_kw={"data-conditional-required": "true"},
    )
    book_format = SelectField(
        _("Book format"),
        choices=[
            ("", _("Select a format")),
            ("ebook", _("E-book")),
            ("audiobook", _("Audiobook")),
        ],
        validators=[validate_book_format],
        render_kw={"data-conditional-required": "true"},
    )
    message = TextAreaField(
        _("Message"),
        [validators.DataRequired(), validators.Length(1, 2048)],
        description=_(
            "Describe your feedback in as much detail as possible. For technical problems, "
            "tell us what you were doing, what happened, and what you expected to happen."
        ),
    )
    # Honeypot field for bot detection
    hp_field = HiddenField("Hidden", [validators.Length(max=20)])
    
    municipality = SelectField(
        _("My home municipality that receives this feedback"),
        choices=[],
        render_kw={
            "class": "form-select",
            "data-control": "select2",
            "data-dropdown-parent": "body",
        },
        validators=[validators.DataRequired(), validate_municipality],
        description=_(
            "Your home municipality's library will be the first to respond. If needed, "
            "they will forward your message to the right recipient."
        ),
    )
    email = EmailField(
        _("Email address, if you want an answer to your feedback (Optional)"),
        [validators.Optional()],
        description=_(
            "Please note that if you do not provide your email address, we cannot "
            "reply to you or ask you for more information."
        ),
    )
    submit = SubmitField(
        _("Send"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.municipality.choices = [
            ("", _("Select a municipality"))
        ] + indexed_municipalities()
