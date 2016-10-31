import httplib, urllib

params = urllib.urlencode({
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
                    "password": "wasserfall"
                }
            }
        }
    }
})

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
conn = httplib.HTTPConnection("http://openstack-controller:35357")
conn.request("POST", "/cgi-bin/query", params, headers)
response = conn.getresponse()
print response.status, response.reason
data = response.read()
conn.close()
print data