from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from os import environ
from datetime import datetime
from functools import wraps
from flask import request, Response

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') or 'sqlite:///test.db'
db = SQLAlchemy(app)


################################################## DATABSE CODE ########################################################


class License(db.Model):
    serial = db.Column(db.String(), primary_key=True)
    key = db.Column(db.String(), unique=True, nullable=False)
    product_name = db.Column(db.String(), nullable=False)
    entity_id = db.Column(db.String(), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)
    number_of_seats = db.Column(db.Integer(), nullable=False)
    expiration_date = db.Column(db.DateTime(), nullable=True)
    is_upgrade = db.Column(db.Boolean, nullable=False)
    upgrade_from_serial = db.Column(db.String(), nullable=True)
    date = db.Column(db.DateTime(), nullable=True)

    def to_json_dict(self):
        return {
            "id": self.serial,
            "product_name": self.product_name,
            "entity_id": self.entity_id,
            "exp": "TODO!!!",
            "number_of_seats": self.number_of_seats,
            "edition": {"en": "Full Edition"}
        }

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


########################################### AUTHENTICATION CODE ########################################################


def check_auth(issuer_id, secret):
    """This function is called to check if a issuer_id /
    secret combination is valid.
    """
    return issuer_id == 'ISSUER_ID_HERE' and secret == 'ISSUER_SECRET_HERE'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        jsonify({"description": "Incorrect Credentials"}),
        401,
        {'WWW-Authenticate': 'Basic realm="Credentials Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


##################################################### ENDPOINTS ########################################################


@app.route("/")
def hello():
    return "Hello World!"

@app.route("/info")
def info():
    licenses = License.query.all()
    return "You have {} licenses!".format(len(licenses))


@app.route("/add_license", methods=["POST"])
@requires_auth
def add_license():
    """See if a license can be added to an entity or whether we should ask more information, or whether we should
    deny the request."""
    pass

@app.route("/remove_license", methods=["POST"])
@requires_auth
def remove_license():
    """See if a license cluster can be removed from an entity. We make sure to note that a license is no longer
    in the entity."""
    payload_dict = request.get_json()

    licenses = []

    for license in payload_dict["licenseCluster"]["licenses"]:
        result = License.query().filter_by(
            serial=license["id"],
            product_name=license["aud"],
            entityId=payload_dict["entityId"]
        ).first()

        if result is not None:
            licenses.append(result)

    if len(licenses) == 0 or len(licenses) == len(payload_dict["licenseCluster"]["licenses"]):

        #Remove the licenses, if they haven't already been removed.
        for license in licenses:
            db.session.delete(license)

        db.session.commit()
        return Response(status=200)
    else:
        #There is an issue with the state of the data.
        return Response(
            jsonify({"description": "The license(s) cannot be currently be removed. Please contact "
                                    "(Dolfinito®)[https://www.dolfinito.com/support] for assistance.",
                     "details": "License key count mismatch"}),
            400
        )

@app.route("/get_license", methods=["GET"])
@requires_auth
def get_license():
    """Return information about a specific license so users can see details about the license."""
    product_name = request.args.get("aud")
    key = request.args.get("key")

    license = License.query().filter_by(key=key, product_name=product_name).first()

    if license is None:
        return Response(
            jsonify({"description": "The license key is not valid"}),
            400
        )
    else:
        return jsonify(license.to_json_dict())


@app.route("/get_products", methods=["GET"])
@requires_auth
def get_products():
    """Return a list of all the products that we, the issuer, support."""
    pass