#! /usr/bin/env python3

import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth
from prettytable import PrettyTable

dnac = {
    "host":"10.19.1.11",
    "username":"admin",
    "password":"Admeen9sisko"
}

dnac_devices = PrettyTable(['Hostname','Platform Id','Serial Number', 'Software Type','Software Version','Reach?', 'Managed?', 'Up Time', 'UUID' ])
dnac_devices.padding_width = 1

# Silence the insecure warning due to SSL Certificate
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


def network_device_list(dnac, token):
    url = "https://{}/api/v1/network-device".format(dnac['host'])
    headers["x-auth-token"] = token
    response = requests.get(url, headers=headers, verify=False)
    data = response.json()
    for item in data['response']:
        dnac_devices.add_row([item["hostname"],item["platformId"],item["serialNumber"], item["softwareType"],item["softwareVersion"],item["reachabilityStatus"], item["managementState"], item["upTime"], item["id"]])


login = dnac_login(dnac["host"], dnac["username"], dnac["password"])
network_device_list(dnac, login)

print(dnac_devices)

