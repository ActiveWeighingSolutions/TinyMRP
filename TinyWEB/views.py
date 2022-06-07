"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template
from TinyWEB import app

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='TinyMRP',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )


# a simple page that says hello
@app.route('/hello')
def hello():
    return 'Hello, World!'

#To register the db initialization in the app
from . import db
db.init_app(app)
    
#To register the authorization blueprint in the app
from . import auth
app.register_blueprint(auth.bp)
    
# To  register the blog blueprint in the app
from . import blog
app.register_blueprint(blog.bp)
app.add_url_rule('/blog', endpoint='index')
    
# To  register the part blueprint in the app
from . import part
app.register_blueprint(part.bp)
app.add_url_rule('/part', endpoint='index')
    
# To  register the home blueprint in the app
from . import home
app.register_blueprint(home.bp)
app.add_url_rule('/', endpoint='index')
