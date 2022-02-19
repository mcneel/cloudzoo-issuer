import base64
import unittest

from app import app, ISSUER_ID, ISSUER_SECRET, License, db

creds = base64.b64encode(f"{ISSUER_ID}:{ISSUER_SECRET}".encode("utf-8")).decode("utf-8")


class JsonTests(unittest.TestCase):
    def test_get_license(self):
        with app.test_client() as c:
            rv = c.get(
                "/get_license?aud=3e200daa-6bf8-470b-bd6a-4f55996052c3&key=LICENSE_KEY_3",
                headers={"Authorization": f"Basic {creds}"},
            )
            json_data = rv.get_json()
            self.assertEqual(json_data.get('id'), 'SERIAL_NO_3')
            self.assertIn('key', json_data)
            self.assertEqual(
                json_data.get("aud"), "3e200daa-6bf8-470b-bd6a-4f55996052c3"
            )
            self.assertIsNotNone(json_data.get('iss'))
            self.assertEqual(json_data.get("exp"), 1546128000)
            self.assertIsNotNone(json_data.get("editions"))
            self.assertEqual(json_data["editions"].get("en"), "Full Edition")
            self.assertGreater(json_data.get('numberOfSeats'), 0)

    def test_get_license_no_auth(self):
        with app.test_client() as c:
            rv = c.get(
                "/get_license?aud=3e200daa-6bf8-470b-bd6a-4f55996052c3&key=LICENSE_KEY_3"
            )
            json_data = rv.get_json()
            self.assertEqual(rv.status_code, 401)
            self.assertEqual(json_data.get("description"), "Incorrect Credentials")
            self.assertEqual(
                rv.headers.get("WWW-Authenticate"), 'Basic realm="Credentials Required"'
            )
    
    def test_get_license_not_valid(self):
        with app.test_client() as c:
            rv = c.get(
                "/get_license?aud=3e200daa-6bf8-470b-bd6a-4f55996052c3&key=LICENSE_KEY_0",
                headers={"Authorization": f"Basic {creds}"},
            )
            json_data = rv.get_json()
            # self.assertEqual(
            #     json_data.get("aud"), "3e200daa-6bf8-470b-bd6a-4f55996052c3"
            # )
            # self.assertIsNotNone(json_data.get("editions"))
            # self.assertEqual(json_data["editions"].get("en"), "Full Edition")
            # self.assertEqual(json_data.get("exp"), 1546128000)

    def test_add_license(self):
        with app.app_context():
            lic = License.query.filter_by(serial='SERIAL_NO_5').first()
            if lic:
                db.session.delete(lic)
            lic = License(
                key="RH50-ABCD-EFGZ-HIJK-LMNO",
                serial="SERIAL_NO_5",
                product_id="PRODUCT-ID-HERE",
                enabled=True,
                entity_id=None,
                date=None,
                expiration_date=None,
            )
            db.session.add(lic)
            db.session.commit()
        payload = {
            "entityId": "9304194021213-|-Group",
            "entityType": "Group",
            "license": {"key": "RH50-ABCD-EFGZ-HIJK-LMNO", "aud": "PRODUCT-ID-HERE"},
            "userInfo": {
                "sub": "43190412048124",
                "email": "marley_the_dog@mcneel.com",
                "com.rhino3d.accounts.emails": [
                    "marley_the_dog@mcneel.com",
                    "marleyz121@gmail.com",
                ],
                "com.rhino3d.accounts.member_groups": [
                    {"id": "9304194021213", "name": "Marley’s Friends LLC"}
                ],
                "com.rhino3d.accounts.admin_groups": [],
                "com.rhino3d.accounts.owner_groups": [],
                "name": "Marley",
                "locale": "en-gb",
                "picture": "http://marley.the.dog.com/images/coolpic.png",
            },
            "precondition": "RH40-ABCD-EFGZ-HIJK-LMNO",
        }
        with app.test_client() as c:
            rv = c.post(
                "/add_license",
                json=payload,
                headers={"Authorization": f"Basic {creds}"},
            )
            self.assertEqual(rv.status_code, 200)
            json_data = rv.get_json()
            self.assertEqual(json_data['licenses'][0]['id'], 'SERIAL_NO_5')
        with app.app_context():
            lic = License.query.filter_by(serial='SERIAL_NO_5').first()
            self.assertEqual(lic.entity_id, '9304194021213-|-Group')
    
    def test_remove_license(self):
        with app.app_context():
            lic = License.query.filter_by(serial='SERIAL_NO_6').first()
            if lic:
                db.session.delete(lic)
            lic = License(
                key='LICENSE_KEY_6',
                serial='SERIAL_NO_6',
                product_id='PRODUCT_ID_HERE',
                enabled=True,
                entity_id='9304194021213-|-Group',
                date=None,
                expiration_date=None
            )
            db.session.add(lic)
            db.session.commit()
        payload = {
            "entityId": "9304194021213-|-Group",
            "entityType": "Group",
            "userInfo": {
                    "sub": "43190412048124",
                    "email": "marley_the_dog@mcneel.com",
                    "name": "Marley",
                    "locale": "en-gb",
                    "picture":"http://marley.the.dog.com/images/coolpic.png"
                },
            "licenseCluster": {
                "licenses": [
                    {
                        "id": "SERIAL_NO_6",
                        "key": "LICENSE_KEY_6",
                        "aud": "PRODUCT_ID_HERE",
                        "iss": ISSUER_ID,
                        "exp": None,
                        "numberOfSeats": 1,
                        "editions": {
                                "en": "Full Edition",
                        }
                    }
                ]
            }
        }
        with app.test_client() as c:
            rv = c.post(
                "/remove_license",
                json=payload,
                headers={"Authorization": f"Basic {creds}"},
            )
            self.assertEqual(rv.status_code, 200)
        with app.app_context():
            lic = License.query.filter_by(serial='SERIAL_NO_6').first()
            self.assertIsNone(lic.entity_id)


if __name__ == "__main__":
    unittest.main()
