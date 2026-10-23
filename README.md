# Intro

This is a simple feedback form that sends support email to configured recipients. Municipality names and feedback recipient addresses are loaded from the Circulation municipality registry.

# Development

Runs at least on `Python 3.11`.

Create a virtual environment with something like 
`python3.11 -m venv venv`
and activate it
`. ./venv/bin/activate`
then install dependencies with
`pip install -r requirements.txt`.
Configure the local Circulation feedback registry endpoint and a development-only shared token. Set the same `FEEDBACK_SERVICE_TOKEN` in both local services, and set `FEEDBACK_MUNICIPALITIES_URL` in this application, for example:

```sh
export FEEDBACK_MUNICIPALITIES_URL=http://127.0.0.1:6500/internal/feedback/municipalities
export FEEDBACK_SERVICE_TOKEN=local-development-only-token
```

Configure the same development-only token in the local Circulation service. Do not use production tokens for local development. Use an authenticated HTTPS service URL in deployed environments. The feedback service caches the last successful municipality response in memory for one day and keeps using it if a refresh fails.

Run the app with
`flask --app app run --debug` when developing.

The app will run in
`http://127.0.0.1:5000/palaute/`

To view the form in web-patron, change the Footer's Feedback link to point to your local instance above.

# Testing

Install the needed dependencies to run unit tests:
`pip install -r requirements-dev.txt`
and run
`python -m pytest`

# Translations

To update the translations, run this:

```
pybabel extract -F babel.cfg -o messages.pot . ; pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . ; pybabel update -i messages.pot -d translations -l fi ; pybabel update -i messages.pot -d translations -l sv ; pybabel update -i messages.pot -d translations -l en
```

Write changes to the translations with:

```
$EDITOR translations/{fi,sv,en}/LC_MESSAGES/messages.po
```

Then run this to compile the changes:

```
pybabel compile -d translations
```

Remember to restart the server for changes to take effect.

Based on this guide: https://python-babel.github.io/flask-babel/#using-translations

