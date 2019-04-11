from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') or 'sqlite:///test.db'
db = SQLAlchemy(app)


################################################## DATABSE CODE ########################################################


class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(), unique=True, nullable=False)
    serial = db.Column(db.String(), unique=True, nullable=False)
    product_name = db.Column(db.String(), nullable=False)
    entity_id = db.Column(db.String(), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)
    date = db.Column(db.DateTime(), nullable=True)

    def __repr__(self):
        return '<License %r>' % self.serial

@app.cli.command()
def create_db():
    db.create_all()

    license_1 = License(
        key="LICENSE_KEY_1",
        serial="SERIAL_NO_1",
        product_name="DOLPHINITO",
        enabled=True
    )

    license_2 = License(
        key="LICENSE_KEY_2",
        serial="SERIAL_NO_2",
        product_name="DOLPHINITO",
        enabled=False
    )

    license_3 = License(
        key="LICENSE_KEY_3",
        serial="SERIAL_NO_3",
        product_name="DOLPHINITO",
        enabled=True,
        entity_id="595959595959595-User",
        date=datetime(year=2018,month=11,day=30)
    )

    db.session.add(license_1)
    db.session.add(license_2)
    db.session.add(license_3)
    db.session.commit()


##################################################### ENDPOINTS ########################################################


@app.route("/")
def hello():
    return "Hello World!"

@app.route("/info")
def info():
    licenses = License.query.all()
    return "You have {} licenses!".format(len(licenses))


@app.route("/add_license", methods=["POST"])
def add_license():
    """See if a license can be added to an entity or whether we should ask more information, or whether we should
    deny the request."""
    pass

@app.route("/remove_license", methods=["POST"])
def remove_license():
    """See if a license can be removed from an entity. We make sure to note that a license is no longer in the entity."""
    pass

@app.route("/get_license", methods=["GET"])
def get_license():
    """Return information about a specific license so users can see details about the license."""
    pass

@app.route("/get_products", methods=["GET"])
def get_products():
    """Return a list of all the products that we, the issuer, support."""
    pass