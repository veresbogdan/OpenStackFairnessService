import requests
import json
from datetime import datetime

from fairness.config_parser import MyConfigParser

# to use this, the fairness user with admin rights has to be created on openStack:
#   $ openstack user create --domain default --password-prompt fairness
#   $ openstack role add --project service --user fairness admin
# then add the credentials to the fairness.ini file.


class IdentityApiConnection(object):
    """ This class is to make Keystone API calls. """

    def __init__(self):
        self.token = None
        self.token_exp = None
        self.token_issued = None

    def _authenticate(self):
        """ The first step to call any other OpenStack API is to authenticate
        with the identity service (keystone). This call returns the X-Auth-Token
        for further calls to other APIs. """

        config = MyConfigParser()
        username = config.config_section_map('keystone_authtoken')['username']
        password = config.config_section_map('keystone_authtoken')['password']
        user_domain_name = config.config_section_map('keystone_authtoken')['user_domain_name']
        project_name = config.config_section_map('keystone_authtoken')['project_name']
        project_domain_name = config.config_section_map('keystone_authtoken')['project_domain_name']

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
                                "name": username,
                                "domain": {
                                    "name": user_domain_name
                                },
                                "password": password
                            }
                        }
                    },
                    "scope": {
                        "project": {
                            "name": project_name,
                            "domain": {"id": project_domain_name}
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
            print("token has been issued!")
            self._authenticate()
        time_now = datetime.utcnow().isoformat()
        if self.token_exp < time_now:
            print "Token Expired at (UTC+1, so substract 1 hour): ", self.token_exp
            print "Time Now (UTC): ", time_now
            print "Issueing a new token because the current one is expired"
            self._authenticate()

    def list_users(self):
        self._check_token()
        url = 'http://openstack-controller:35357/v3/users'
        headers = {'X-Auth-Token': self.token}
        r = requests.get(url, headers=headers)
        # print r.headers
        # print r.text
        # print r.status_code
        json_text = json.loads(r.text)
        user_dict = {}
        for i in range(len(json_text["users"])):
            user = str(json_text['users'][i]['name'])
            user_id = str(json_text['users'][i]['id'])
            user_dict[user_id] = user
        return user_dict

    def list_projects(self):
        self._check_token()
        url = 'http://openstack-controller:35357/v3/projects'
        headers = {'X-Auth-Token': self.token}
        r = requests.get(url, headers=headers)
        json_text = json.loads(r.text)
        print r.text

    def get_quotas(self, user):
        self._check_token()
        url = 'http://openstack-controller:8774/v2.1/os-quota-sets/e655d37b5181407281277b8fb1eef3f4?user_id=' + user
        headers = {'X-Auth-Token': self.token}
        r = requests.get(url, headers=headers)
        json_text = json.loads(r.text)
        cores = json_text['quota_set']['cores']
        ram = json_text['quota_set']['ram']  # in MB
        return cores, ram

    def get_all_vms(self, user_dict):
        self._check_token()
        url = 'http://openstack-controller:8774/v2.1/servers/detail?all_tenants=1'
        headers = {'X-Auth-Token': self.token}
        r = requests.get(url, headers=headers)
        json_text = json.loads(r.text)
        # print r.headers
        # print r.text
        # print r.status_code
        list_of_all_vms = []
        for i in range(len(json_text['servers'])):
            vm_dict = {}
            instance_status = json_text['servers'][i]['status']
            if instance_status == "ACTIVE":
                user_id = json_text['servers'][i]['user_id']
                user_name = user_dict[user_id]
                instance_name = json_text['servers'][i]['OS-EXT-SRV-ATTR:instance_name']
                host = json_text['servers'][i]['OS-EXT-SRV-ATTR:host']
                vm_dict[str(instance_name)] = [str(user_name), str(host)]
                list_of_all_vms.append(vm_dict)
        return list_of_all_vms
