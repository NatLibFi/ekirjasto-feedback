import os
import getpass
from flask import Flask
from flask_mail import Mail

app = Flask(__name__)

# Turn this to true to disable sending emails
app.config["TESTING"] = False
app.config["EMAILS_CSV"] = "emails.csv"
# Default receiver for feedback that has no home municipality or the sender refuses to say
app.config["DEFAULT_RECEIVER"] = "e-kirjasto-tekniikka@helsinki.fi"
# This recipient always receives the emails regardless of which municipality is chosen
app.config["ALWAYS_RECIPIENT"] = "e-kirjasto-tekniikka@helsinki.fi"

app.config["LANGUAGES"] = {
    "en": "English",
    "fi": "Finnish",
    "sv": "Swedish",
}

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = os.environ["MAIL_USERNAME"]
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)
