from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from os import environ
import datetime
import time
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
    upgrade_from_key = db.Column(db.String(), nullable=True)
    date = db.Column(db.DateTime(), nullable=True)

    def to_json_dict(self):
        return {
            "id": self.serial,
            "product_name": self.product_name,
            "entity_id": self.entity_id,
            "exp": time.mktime(self.expiration_date.timetuple()),
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
        date=datetime.datetime(year=2018,month=11,day=30)
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
    deny the request. Note that you may have additional requirements depending on your business requirements."""
    payload_dict = request.get_json()
    product_name = payload_dict.get("aud")
    key = payload_dict.get("key")
    entity_id = payload_dict.get("entityId")
    precondition = payload_dict.get("precondition")

    license = License.query().filter_by(key=key, product_name=product_name).first()


    #Add non-existing license.
    if license is None:
        return Response(
            jsonify({"description": "The license key '{}' is not a valid license".format(key)}),
            409
        )

    #Add disabled license.
    if not license.enabled:
        return Response(
            jsonify({"description": "The license key '{}' cannot be added at this time. Please contact "
                                    "(Dolfinito®)[https://www.dolfinito.com/support] for assistance.".format(key)}),
            409
        )

    #Add license to different entity.
    if license.entity_id is not None and license.entity_id != entity_id:
        return Response(
            jsonify({"description": "The license key '{}' has already been validated by someone else. Please contact "
                                    "(Dolfinito®)[https://www.dolfinito.com/support] for assistance.".format(key)}),
            409
        )


    #Add upgrade
    if license.is_upgrade:
        #Missing precondition.
        if precondition is None:
            return Response(
                jsonify({"description": "Please enter a previous license key to upgrade from."}),
                428
            )

        previous_key = License.query().filter_by(key=precondition).first()

        #Non-existing previous license key
        if previous_key is None:
            return Response(
                jsonify({"description": "The license key '{}' is not a valid license. "
                                        "Please enter a different license to upgrade from.".format(precondition)}),
                412
            )

        #Previous license already upgraded
        if license.upgrade_from_key is not None and license.upgrade_from_key != precondition:
            return Response(
                jsonify({"description": "The license key '{}' has already been upgraded to a different license key. Please contact "
                                        "(Dolfinito®)[https://www.dolfinito.com/support] for assistance.".format(precondition)}),
                412
            )

        #Previous license is a non-validated upgrade.
        if previous_key.is_upgrade and previous_key.entity_id is None:
            return Response(
                jsonify({
                            "description": "The license key '{}' cannot be used to upgrade. Please enter "
                                           "a different license key to upgrade from.".format(precondition)}),
                412
            )

        #Valid upgrade. We make sure to cluster all licenses.
        licenses = [previous_key.to_json_dict(), license.to_json_dict()]
        a_license = previous_key

        while a_license.upgrade_from_key is not None:
            a_license = License.query().filter_by(key=a_license.upgrade_from_key).first()
            licenses.append(a_license.to_json_dict())
    else:
        licenses = [license.to_json_dict()]

    #Add full license
    return jsonify({"licenses": [licenses]})

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