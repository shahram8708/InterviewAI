"""
Entry point for the AI Mock Interview Platform.
Load environment variables FIRST, before any app imports.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    # use_reloader=False is deliberate: the auto-reloader spawns a second process,
    # which causes startup logic (database init) to run twice and produces
    # confusing duplicate behavior in development.
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=(os.environ.get('FLASK_ENV') == 'development'),
        use_reloader=False
    )
