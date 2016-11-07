import requests
import json
import datetime

# to use this, the fairness user with admin rights has to be created on openStack:
#   $ openstack user create --domain default --password-prompt fairness // use "wasserfall" as the password
#   $ openstack role add --project service --user fairness admin

# TODO: import config file and extract username and password for the payload
# TODO: Should the domain be looked up with a diffenrent API call? But which one? And how to get the initial token?


class IdentityApiConnection(object):
    """ This class is to make Keystone API calls. """

    def __init__(self):
        self.token = None
        self.token_exp = None
        self.token_issued = None

    def authenticate(self):
        """ The first step to call any other OpenStack API is to authenticate
        with the identity service (keystone). This call returns the X-Auth-Token
        for further calls to other APIs. """

        if self.token is None:
            url = 'http://openstack-controller:35357/v3/auth/tokens'
            payload = {
                "auth": {
                    "identity": {
                        "methods": [
                            "password"
                        ],
                        "password": {
                            "user": {
                                "name": "fairness",
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
            self.token = r.headers['X-Subject-Token']
            json_text = json.loads(r.text)
            self.token_exp = json_text['token']['expires_at']
            self.token_issued = json_text['token']['issued_at']

    def _check_token(self):
        if self.token is None:
            self.authenticate()
        time_now = datetime.datetime.utcnow().isoformat()
        if self.token_exp < time_now:
            print "Token Expired at (UTC+1, so substract 1 hour): ", self.token_exp
            print "Time Now (UTC): ", time_now
            print "Issueing a new token because the current one is expired"
            self.authenticate()

    def list_users(self):
        self._check_token()
        url = 'http://openstack-controller:35357/v3/users'
        headers = {'X-Auth-Token': self.token}
        r = requests.get(url, headers=headers)
        json_text = json.loads(r.text)
        user_list = []
        for i in range(len(json_text["users"])):
            user_list.append(json_text['users'][i]['name'])
        return user_list

    def list_projects(self):
        self._check_token()
        url = 'http://openstack-controller:35357/v3/projects'
        headers = {'X-Auth-Token': self.token}
        r = requests.get(url, headers=headers)
        json_text = json.loads(r.text)
        print r.text
