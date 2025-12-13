from app import create_app
from flask_frozen import Freezer
from dotenv import load_dotenv

load_dotenv()

app = create_app()
app.config['FREEZER_RELATIVE_URLS'] = True

freezer = Freezer(app)

if __name__ == '__main__':
    freezer.freeze()
