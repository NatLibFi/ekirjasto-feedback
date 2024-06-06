import csv
from config import app
from flask_babel import lazy_gettext as _
from flask import Flask


def indexed_municipalities():
    """
    turns this:
    [("example@example.org", "City of Exemplars")]
    into this:
    [(0, "City of Exemplars")]
    You can use index_to_email to reverse it
    """
    munis = []
    i = 0
    for email, muni in municipalities:
        munis.append((i, muni))
        i += 1
    return munis


def index_to_email(index):
    return municipalities[index][0]


def index_to_name(index):
    return municipalities[index][1]


def get_emails():
    with open(app.config["EMAILS_CSV"], encoding="utf-8", newline="") as csvfile:
        email_reader = csv.reader(
            csvfile,
            delimiter=",",
        )
        emails = []
        for row in email_reader:
            email = row[0]
            name = row[1]
            emails.append((email, name))

    # Sort by the second element in a list of tuples because that's where the municipality names are
    emails = sorted(emails, key=lambda x: x[1])

    # Decorate the emails with some custom values that aren't municipalities
    emails.append(
        (
            app.config["DEFAULT_RECEIVER"],
            _("My home municipality is missing from this list"),
        ),
    )
    emails.append((app.config["DEFAULT_RECEIVER"], _("I don't want to say")))

    return emails


# Note how this is only read once per startup so you need to restart for a new list to be used
municipalities = get_emails()
