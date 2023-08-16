from flask import Flask, render_template
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from form import AddUserForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-is-secr3t'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///sharecipe'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

# connect_db(app)

@app.route("/")
def home_page():
    return render_template('homepage.html')
