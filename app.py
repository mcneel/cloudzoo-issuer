from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
from os import environ
import datetime
import time
from functools import wraps
from flask import request
from flask_talisman import Talisman

app = Flask(__name__)
Talisman(app)
db_uri = environ.get('DATABASE_URL')
if not db_uri:
    db_uri = 'sqlite:///test.db' # local dev
elif db_uri.startswith("postgres://"):
    # https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS'] = False

ISSUER_ID = environ.get('ISSUER_ID')
ISSUER_SECRET = environ.get('ISSUER_SECRET')
ISSUER_NAME = environ.get('ISSUER_NAME') or "Dolfinito®"
ISSUER_SUPPORT_URL = environ.get('ISSUER_SUPPORT_URL') or "https://www.dolfinito.com/support"

################################################## DATABSE CODE ########################################################


class License(db.Model):
    __tablename__ = 'licenses'
    """This object represents a License object for your product. See https://developer.rhino3d.com/guides/rhinocommon/cloudzoo/cloudzoo-license/ for details on a license object."""
    serial = db.Column(db.String(), primary_key=True)
    key = db.Column(db.String(), unique=True, nullable=False)
    product_id = db.Column(db.String(), nullable=False)
    entity_id = db.Column(db.String(), nullable=True)
    enabled = db.Column(db.Boolean, nullable=False)
    number_of_seats = db.Column(db.Integer(), nullable=False, default=1)
    expiration_date = db.Column(db.DateTime(), nullable=True)
    is_upgrade = db.Column(db.Boolean, nullable=False, default=False)
    upgrade_from_key = db.Column(db.String(), nullable=True)
    date = db.Column(db.DateTime(), nullable=True, onupdate=datetime.datetime.utcnow)

    def to_json_dict(self):
        return {
            "id": self.serial,
            "key": self.key,
            "aud": self.product_id,
            "iss": ISSUER_ID,
            "exp": int(time.mktime(self.expiration_date.timetuple())) if self.expiration_date is not None else None,
            "numberOfSeats": self.number_of_seats,
            "editions": {"en": "Full Edition"},
            "metadata": None
        }

    def __repr__(self):
        return '<License %r>' % self.serial

@app.cli.command()
def create_db():
    """This method simply creates some dummy licenses for demo purposes and inserts them into the database."""
    db.create_all()

    license_1 = License(
        key="LICENSE_KEY_1",
        serial="SERIAL_NO_1",
        product_id="3e200daa-6bf8-470b-bd6a-4f55996052c3",
        enabled=True
    )

    license_2 = License(
        key="LICENSE_KEY_2",
        serial="SERIAL_NO_2",
        product_id="3e200daa-6bf8-470b-bd6a-4f55996052c3",
        enabled=False
    )

    license_3 = License(
        key="LICENSE_KEY_3",
        serial="SERIAL_NO_3",
        product_id="3e200daa-6bf8-470b-bd6a-4f55996052c3",
        enabled=True,
        entity_id="595959595959595-|-User",
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
    return issuer_id == ISSUER_ID and secret == ISSUER_SECRET

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return (
        jsonify({"description": "Incorrect Credentials"}),
        401,
        {'WWW-Authenticate': 'Basic realm="Credentials Required"'})

def requires_auth(f):
    """A convenience decorator that makes it simple to enforce authentication on enddpoints."""
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
    deny the request. Note that you may have additional requirements depending on your business requirements.
    See more info about this endpoint at: https://developer.rhino3d.com/guides/rhinocommon/cloudzoo/cloudzoo-implement-http-callbacks/#post-add_license"""
    payload_dict = request.get_json()
    product_id = payload_dict['license'].get("aud")
    key = payload_dict['license'].get("key")
    entity_id = payload_dict.get("entityId")
    precondition = payload_dict.get("precondition")

    license = License.query.filter_by(key=key, product_id=product_id).first()

    #Add non-existing license.
    if license is None:
        return (
            jsonify({"description": "The license key '{}' is not a valid license".format(key)}),
            409
        )

    #Add disabled license.
    if not license.enabled:
        return (
            jsonify({"description": "The license key '{}' cannot be added at this time. Please contact "
                                    "[{}]({}) for assistance.".format(key, ISSUER_NAME, ISSUER_SUPPORT_URL)}),
            409
        )

    #Add license to different entity.
    if license.entity_id is not None and license.entity_id != entity_id:
        return (
            jsonify({"description": "The license key '{}' has already been validated by someone else. Please contact "
                                    "[{}]({}) for assistance.".format(key, ISSUER_NAME, ISSUER_SUPPORT_URL)}),
            409
        )


    #Add upgrade
    if license.is_upgrade:
        #Missing precondition.
        if precondition is None:
            return (
                jsonify({"description": "Please enter a previous license key to upgrade from."}),
                428
            )

        previous_key = License.query.filter_by(key=precondition).first()

        #Non-existing previous license key
        if previous_key is None:
            return (
                jsonify({"description": "The license key '{}' is not a valid license. "
                                        "Please enter a different license to upgrade from.".format(precondition)}),
                412
            )

        #Previous license already upgraded
        if license.upgrade_from_key is not None and license.upgrade_from_key != precondition:
            return (
                jsonify({"description": "The license key '{}' has already been upgraded to a different license key. Please contact "
                                        "[{}]({}) for assistance.".format(precondition, ISSUER_NAME, ISSUER_SUPPORT_URL)}),
                412
            )

        #Previous license is a non-validated upgrade.
        if previous_key.is_upgrade and previous_key.entity_id is None:
            return (
                jsonify({
                            "description": "The license key '{}' cannot be used to upgrade. Please enter "
                                           "a different license key to upgrade from.".format(precondition)}),
                412
            )

        #Valid upgrade. We make sure to cluster all licenses.
        licenses = [previous_key.to_json_dict(), license.to_json_dict()]
        a_license = previous_key

        while a_license.upgrade_from_key is not None:
            a_license = License.query.filter_by(key=a_license.upgrade_from_key).first()
            licenses.append(a_license.to_json_dict())
    else:
        license.entity_id = entity_id
        license.date = datetime.datetime.utcnow()
        db.session.commit()
        licenses = [license.to_json_dict()]

    return jsonify({"licenses": licenses})

@app.route("/remove_license", methods=["POST"])
@requires_auth
def remove_license():
    """See if a license cluster can be removed from an entity. We make sure to note that a license is no longer
    in the entity. See more info about this endpoint at: https://developer.rhino3d.com/guides/rhinocommon/cloudzoo/cloudzoo-implement-http-callbacks/#post-remove_license"""
    payload_dict = request.get_json()

    licenses = []

    for license in payload_dict["licenseCluster"]["licenses"]:
        result = License.query.filter_by(
            serial=license["id"],
            product_id=license["aud"],
            entity_id=payload_dict["entityId"]
        ).first()

        if result is not None:
            licenses.append(result)

    if len(licenses) == 0 or len(licenses) == len(payload_dict["licenseCluster"]["licenses"]):

        # remove the entity id from the licenses
        for license in licenses:
            license.entity_id = None
            license.date = datetime.datetime.utcnow()

        db.session.commit()
        return ('', 200)
    else:
        #There is an issue with the state of the data.
        return (
            jsonify({"description": "The license(s) cannot be currently be removed. Please contact "
                                    "[{}]({}) for assistance.".format(ISSUER_NAME, ISSUER_SUPPORT_URL),
                     "details": "License key count mismatch"}),
            400
        )

@app.route("/get_license", methods=["GET"])
@requires_auth
def get_license():
    """Return information about a specific license so users can see details about the license.
    See more info about this endpoint at https://developer.rhino3d.com/guides/rhinocommon/cloudzoo/cloudzoo-implement-http-callbacks/#get-get_license"""
    product_id = request.args.get("aud")
    key = request.args.get("key")

    license = License.query.filter_by(key=key, product_id=product_id).first()

    if license is None:
        return (
            jsonify({"description": "The license key is not valid"}),
            400
        )
    else:
        return jsonify(license.to_json_dict())
