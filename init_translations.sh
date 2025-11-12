#!/bin/bash
# Initialize translations for Flask-Babel

# Extract translatable strings
pybabel extract -F babel.cfg -k _ -o messages.pot .

# Initialize translation files for each language
pybabel init -i messages.pot -d translations -l hi
pybabel init -i messages.pot -d translations -l mr
pybabel init -i messages.pot -d translations -l ta
pybabel init -i messages.pot -d translations -l te
pybabel init -i messages.pot -d translations -l bn
pybabel init -i messages.pot -d translations -l gu

echo "Translation files initialized. Edit translations/*/LC_MESSAGES/messages.po and run: pybabel compile -d translations"

