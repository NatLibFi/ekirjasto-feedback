# Intro

This is a simple feedback form that is supposed to be used to send support email to recipients according to a csv.

# Important

If you change the municipalities emails csv file remember to restart the server because the list is only read at startup.

# Development

Runs at least on `Python 3.11`.

Create a virtual environment with something like 
`python3.11 -m venv venv`
and activate it
`. ./venv/bin/activate`
then install dependencies with
`pip install -r requirements.txt`.
Then create a `emails.csv` a few names and emails
```sh
test@testcity.org,Test City
info@sampletown.org,Sample Town
```
and run the app with
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

