import os
import getpass
from flask import Flask
from dotenv import dotenv_values, load_dotenv

load_dotenv()

app = Flask(__name__)

config = dotenv_values()
app.config.from_mapping(config)

app.config["LANGUAGES"] = {
    "en": "English",
    "fi": "Finnish",
    "sv": "Swedish",
}

# Allow session cookie in cross-origin iframe
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True
