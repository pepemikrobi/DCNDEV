#!/usr/bin/python

import sys
import requests
from requests.auth import HTTPBasicAuth
import json

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
            'content-type': "application/json",
            'x-auth-token': ""
}

def dnac_login(host, username, password):
    url = "https://{}/api/system/v1/auth/token".format(host)
    response = requests.request("POST", url, auth=HTTPBasicAuth(username, password),
                                headers=headers, verify=False)
    return response.json()["Token"]

def dnac_get_aaa_servers (host):
    url = f"https://{host}/dna/intent/api/v1/authentication-policy-servers"
    response = requests.request("GET", url, headers=headers, verify=False)
    return (response)


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print ("""Usage:
        ise_check.py <pod_number> <user> <password>
    
        where <pod_number> is in 1...5""")
        exit(1)

    pod = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    #print (f'Arguments: pod {pod}, user {username}, pass {password}')

    host = "10.1" + pod + ".1.11"
    token = dnac_login(host, username, password)
    headers["x-auth-token"] = token
    #print (token)
    ise_data = dnac_get_aaa_servers(host)
    print (ise_data.json())
    print (json.dumps(ise_data.json(), indent=4))

