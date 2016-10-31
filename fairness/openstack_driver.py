import requests
url = 'http://openstack-controller:35357/v3/'
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
                        "name": "Default"
                    },
                    "password": "devstacker"
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
r.text
r.status_code