"""
main.py

App Engine entry point.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')


from app import app
if app.config['DEBUG']:
    # Run debugged app
    app.debug=True

