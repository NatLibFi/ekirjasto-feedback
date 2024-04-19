import os
import getpass
from flask import Flask
from flask_mail import Mail
from dotenv import dotenv_values, load_dotenv
config = dotenv_values(".env")
load_dotenv()

app = Flask(__name__)

# When True, emails are not sent
app.config["TESTING"] = bool(os.environ.get("TESTING") == True)
# Root path for where the app lives so that we can have it in example.org/ or
# example.org/feedback/ or example.org/something/else/feedback
app.config["ROOT_PATH"] = os.environ.get("ROOT_PATH", "/")
# Location of the csv file that contains emails and municipality names.
app.config["EMAILS_CSV"] = os.environ.get("EMAILS_CSV", "emails.csv")
# Default receiver for feedback that has no home municipality or the sender refuses to say
app.config["DEFAULT_RECEIVER"] = os.environ.get("EMAIL_DEFAULT_RECEIVER", "e-kirjasto-tekniikka@helsinki.fi")
# A copy of the emails is always sent to this address
app.config["ALWAYS_RECIPIENT"] = os.environ.get("ALWAYS_RECIPIENT", "e-kirjasto-tekniikka@helsinki.fi")
app.config["MAIL_SENDER"] = os.environ.get("MAIL_SENDER", "e-kirjasto-tekniikka@helsinki.fi")
app.config["BACKUP_FILE"] = os.environ.get("BACKUP_FILE", "feedback.backup")

app.config["LANGUAGES"] = {
    "en": "English",
    "fi": "Finnish",
    "sv": "Swedish",
}

app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = os.environ.get("MAIL_PORT", 465)
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "usr")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "pss")
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", False)
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", True)

mail = Mail(app)
