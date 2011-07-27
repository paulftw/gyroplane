"""
main.py

App Engine entry point.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')


def main():
    from app import app
    if app.config['DEBUG']:
        # Run debugged app
        from werkzeug_debugger_appengine import get_debugged_app
        from wsgiref.handlers import CGIHandler
        app.debug=True
        debugged_app = get_debugged_app(app)
        CGIHandler().run(debugged_app)
    else:
        # Run production app
        from google.appengine.ext.webapp.util import run_wsgi_app
        run_wsgi_app(app)


# Use App Engine app caching
if __name__ == "__main__":
    main()
