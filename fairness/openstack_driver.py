import requests
import json

# to use this, the fairness user with admin rights has to be created on openStack:
#   $ openstack user create --domain default --password-prompt fairness // use "wasserfall" as the password
#   $ openstack role add --project service --user fairness admin


class IdentityApiConnection(object):
    """ This class is to make OpenStack API calls. """

    def __init__(self):
        pass

    @staticmethod
    def authenticate():
        """ The first step to call any other OpenStack API is to authenticate
        with the identity service (keystone). This call returns the X-Auth-Token
        for further calls to other APIs. """
        url = 'http://openstack-controller:35357/v3/auth/tokens'
        payload = {
            "auth": {
                "identity": {
                    "methods": [
                        "password"
                    ],
                    "password": {
                        "user": {
                            "name": "admin",
                            "domain": {
                                "name": "default"
                            },
                            "password": "wasserfall" # to take from config file: name, psw and domain.
                        }
                    }
                }
            }
        }
        # POST with JSON
        r = requests.post(url, data=json.dumps(payload))
        return r.headers['X-Subject-Token']

    @staticmethod
    def list_users(token):
        url = 'http://openstack-controller:35357/v3/users'
        headers = {'X-Auth-Token': token}
        r = requests.get(url, headers=headers)
        print r.text
        print r.status_code
        # json_data = json.dumps(r.text)
        # item_dict = json.loads(json_data)
        print r.text[0]

