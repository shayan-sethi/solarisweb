# Translation Guide

This Flask app supports multiple Indian languages using Flask-Babel.

## Supported Languages

- English (en)
- Hindi (हिंदी)
- Marathi (मराठी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Bengali (বাংলা)
- Gujarati (ગુજરાતી)

## Setting Up Translations

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Extract translatable strings:**
   ```bash
   pybabel extract -F babel.cfg -k _ -o messages.pot .
   ```

3. **Initialize translation files (first time only):**
   ```bash
   ./init_translations.sh
   ```
   Or manually:
   ```bash
   pybabel init -i messages.pot -d translations -l hi
   pybabel init -i messages.pot -d translations -l mr
   # ... repeat for other languages
   ```

4. **Edit translation files:**
   Edit `translations/{lang}/LC_MESSAGES/messages.po` and add translations for each `msgstr ""` entry.

5. **Compile translations:**
   ```bash
   pybabel compile -d translations
   ```

6. **Update translations (after adding new strings):**
   ```bash
   pybabel extract -F babel.cfg -k _ -o messages.pot .
   pybabel update -i messages.pot -d translations
   # Then edit and compile as above
   ```

## Using Translations in Templates

Wrap translatable strings with `{{ _('Your text here') }}`:

```jinja2
<h1>{{ _('Welcome to Solaris') }}</h1>
<p>{{ _('Smart rooftop solar estimator') }}</p>
```

## Using Translations in Python Code

```python
from flask_babel import gettext as _

flash(_('Language changed successfully.'), 'success')
```

## Language Toggle

Users can change language using the dropdown in the header. The selection is stored in the session and persists across pages.

