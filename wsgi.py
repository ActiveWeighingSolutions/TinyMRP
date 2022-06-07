"""
This script runs the TinyWEB to be used as an entry point to our application by gunicorn
"""

from TinyWEB import app


if __name__ == '__main__':
    
    app.run()
