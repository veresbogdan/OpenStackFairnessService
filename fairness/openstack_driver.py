import requests
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
                    "password": "wasserfall"
                }
            }
        }
    }
}

# POST with form-encoded data
# r = requests.post(url, data=payload)

# POST with JSON
import json
r = requests.post(url, data=json.dumps(payload))

# Response, status etc
print r.text
print r.status_code
