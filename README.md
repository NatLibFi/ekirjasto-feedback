# Intro

This is a simple feedback form that is supposed to be used to send support email to recipients according to a csv.

# Important

If you change the municipalities emails csv file remember to restart the server because the list is only read at startup.

# Development

Create a virtual environment with something like 
`python -m venv venv`
then install dependencies with
`pip install -r requirements.txt`.
and run the app with
`flask --app app run --debug` when developing.

# Translations

To update the translations, run this:

```
pybabel extract -F babel.cfg -o messages.pot . ; pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot . ; pybabel update -i messages.pot -d translations -l fi ; pybabel update -i messages.pot -d translations -l sv ; pybabel update -i messages.pot -d translations -l en
```

Write changes to the translations with
```
$EDITOR translations/{fi,sv,en}/LC_MESSAGES/messages.po

```
pybabel compile -d translations
```

Remember to restart the server for changes to take effect.

Based on this guide: https://python-babel.github.io/flask-babel/#using-translations

