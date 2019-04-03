from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') or 'sqlite:///test.db'
db = SQLAlchemy(app)

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(), unique=True, nullable=False)
    serial = db.Column(db.String(), unique=True, nullable=False)
    product_name = db.Column(db.String(), nullable=False)
    entity_id = db.Column(db.String(), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)
    date = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return '<License %r>' % self.serial

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/info")
def info():
    licenses = License.query.all()
    return "You have {} licenses!".format(len(licenses))
