# DNA Center SDK example for designing site parameters
# A part of Developing with Cisco Networks DevOps Style (DCNDEV) Course
# Author: robert.slaski@gmail.com

import time
import glob
import sys
import json
import yaml
from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from dnacentersdk import DNACenterAPI
from dnacentersdk.exceptions import ApiError, AccessTokenError

console = Console()
table = Table(show_header=True, header_style="bold green")
global dnac
global steps
apply_settings = True

# A header option for synchronous API run
SYNC =  { "__runsync" : True }

# Parse command-line input data
def parse_input(argv):
    # Retrieve pod argument
    if len(argv) != 2:
        print ("""Usage:
        dnac_site.py <pod_number> 
    
        where <pod_number> is in 1...5\n
        set password using shell with \'export DNA_CENTER_PASSWORD='AdmeenXsisko'\'
        where X is the pod number\n""")
        exit(1)

    try:
        pod = int(argv[1])
    except:
        print ("Invalid pod parameter")
        exit (1)
    else: 
        if (pod <1 or pod>5):
            print ("Invalid pod number")
            exit (1)
        else:
            return pod


# Authenticate, get token, return DNACenterAPI object
def get_connected(pod):
    fqdn = f'https://pod{pod}-dnac.sdn.lab'
    console.print(f"[bold yellow] Retrieving token from {fqdn}...", end="")
    try:
        dnac = DNACenterAPI(base_url=fqdn, username='admin', verify=False)
    except AccessTokenError as err:
        console.print(f'[blink bold red] ERROR: Token invalid!')
        exit(1)
    except ApiError as err:
        console.print(f'[blink bold red] ERROR: {err}')
        exit(1)
    else:
        console.print(f'[green] [OK]\n')
        return dnac

# Set-up embedded data
def setup_data(pod):
    console.print(f"[bold yellow] Creating IP Pool data structure...[green] [OK]\n")
    return \
    {
        "ipPoolName":f"POD{pod}_POOL_UNDERLAY",
        "type": "Generic",
        "ipPoolCidr":f"10.1{pod}.64.0/18",
        "dhcpServerIps": [
        "10.16.2.3"
        ],
        "dnsServerIps": [
        "8.8.8.8"
        ],
        "IpAddressSpace": "IPv4"
    }, \
    {
        "ipPoolName":f"POD{pod}_POOL_OVERLAY",
        "type": "Generic",
        "ipPoolCidr":f"10.1{pod}.128.0/17",
        "dhcpServerIps": [
        "10.16.2.3"
        ],
        "dnsServerIps": [
        "8.8.8.8"
        ],
        "IpAddressSpace": "IPv4"
    }, \
    {
        "ipPoolName":f"POD{pod}_POOL6_OVERLAY",
        "type": "Generic",
        "ipPoolCidr":f"2001:db8:1{pod}::/48",
        "dnsServerIps": [
        "2001:4860:4860::8888"
        ],
        "IpAddressSpace": "IPv6"
    }

        
# Create a new site
def create_new_site(site):
    global fabric_site_id
    console.print(f"[yellow] Creating site, type {site['type']}, data {site['site']}", end="")

    try:
        resp = dnac.sites.create_site(payload=site, headers=SYNC)
    except ApiError as err:
        console.print (f"[blink bold red] ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    else:
        console.print(f'[green] [OK]\n')        


# Create sites from directory files
def create_sites_from_files (files):
    console.print (f'[yellow] Loading file list...', end="")
    try:
        files = glob.glob(files) 
    except:
        console.print(f'[blink bold red] ERROR: File listing error')
        exit (1)

    files.sort()
    console.print(f'[green] [OK]\n')

    for f in files:
        console.print (f'[yellow] Opening file \"{f}\"', end="")
        with open(f, 'r') as fhandle:
            console.print(f'[green] [OK]')
            file_data = json.load(fhandle)
            create_new_site(file_data)

    #console.print(f'[bold yellow] Create sites from files [green] [OK]\n')


# Get site info by name
def get_site_info(site_name):
    try:
        site_info = dnac.sites.get_site(name=site_name)
    except ApiError as err:
        console.print (f"[blink bold red] ERROR: {err}")
        exit (1)
    else:
        console.print(f'[green] [OK]')
        return site_info
    

# Create a set of global pools    
def create_global_pools(pools):

    try:
        site_info = dnac.network_settings.create_global_pool(settings=pools, headers=SYNC)
    except TypeError as err:
        console.print (f"[blink bold red] Type ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    except ApiError as err:
        console.print (f"[blink bold red] API ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    else:
        console.print(f'[green] [OK]')
        return site_info


# Create a set of global pools    
def get_global_pools():
    try:
        pool = dnac.network_settings.get_global_pool()
    except ApiError as err:
        console.print (f"[blink bold red] API ERROR: {err}")
        exit (1)
    else:
        console.print(f'[green] [OK]')
        return pool


# Display a table of global IP Pools
def display_global_pools(global_pools):
    table.add_column("Pool Name")
    table.add_column("Prefix")
    table.add_column("DNS IP")    
    for gp in global_pools:
        table.add_row (gp["ipPoolName"], gp["ipPoolCidr"], gp["dnsServerIps"][0] )
    console.print(table)


# Reserve a pool at location    
def reserve_pool(net_id, pod, global_pool, global_pool6, site_id):
    console.print(f"[yellow] Reserve pool NET{net_id} from {global_pool['ipPoolCidr']} and {global_pool6['ipPoolCidr']}...", end="")
    try:
        dnac.network_settings.reserve_ip_subpool(name=f"NET{net_id}", type="LAN", \
                                                ipv4GlobalPool=global_pool["ipPoolCidr"], ipv6GlobalPool=global_pool6["ipPoolCidr"], site_id=site_id, \
                                                ipv4Prefix=True, ipv4Subnet=f"10.1{pod}.{net_id}.0", ipv4PrefixLength=24, ipv4GateWay=f"10.1{pod}.{net_id}.1", \
                                                ipv4DhcpServers=["10.16.2.3"], ipv4DnsServers=["10.16.2.3", "10.16.2.6"], \
                                                ipv6AddressSpace=True, ipv6Prefix=True, \
                                                ipv6Subnet=f"2001:db8:1{pod}:{net_id}::", ipv6PrefixLength=64, ipv6GateWay=f"2001:db8:1{pod}:{net_id}::1", \
                                                ipv6DnsServers=["2001:4860:4860::8888"])
    except TypeError as err:
        console.print (f"[blink bold red] Type ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    except MalformedRequest as err:
        console.print (f"[blink bold red] Type ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    except ApiError as err:
        console.print (f"[blink bold red] API ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    else:
        console.print(f'[green] [OK]')


# Update network settings for a site
def create_network_settings(site):

    s = \
    {
        "dhcpServer": ["10.16.2.3"],
        "dnsServer": {
            "domainName": "sdn.lab",
            "primaryIpAddress": "10.16.2.3",
            "secondaryIpAddress": "10.16.2.6"
        },
        "timezone" : "Europe/Warsaw",
        "ntpServer" : [ f"10.1{pod}.1.252", f"10.1{pod}.1.253" ],
        "network_aaa": {
            "servers": "ISE",
            "ipAddress": f"10.1{pod}.1.13",
            "network": f"10.1{pod}.1.13",
            "protocol": "TACACS"
        },
        "clientAndEndpoint_aaa": {
           "servers": "ISE",
           "ipAddress": f"10.1{pod}.1.13",
           "network": f"10.1{pod}.1.13",
           "protocol": "RADIUS"
        }
        #"messageOfTheday": {
        #    "bannerMessage": "##### This is SDN Lab ###\n### You have been warned ###",
        #    "retainExistingBanner": "False",
        #    "doesNotWorkAnyhow": "True"
        #}
    }

    try:
        dnac.network_settings.create_network(settings=s, site_id=site, headers=SYNC)
    except ApiError as err:
        console.print (f"[blink bold red] ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    else:
        console.print(f'[green] [OK]\n')     


# Create network device credentials
def create_network_credentials(pod):

    s = \
    {
        "cliCredential": [
            {
                "description": f"POD{pod}_CLI_credentials",
                "username": "cliadmin",
                "password": f"Admin{pod}sisko$",
                "enablePassword": f"Admin{pod}sisko$"
            }
        ],
        "snmpV2cRead": [
            {
            "description": "SNMP_RO",
            "readCommunity": "cisco"
            }
        ],
        "snmpV2cWrite": [
            {
            "description": "SNMP_RW",
            "writeCommunity": f"Admin{pod}sisko$"
            }
        ]
    }

    try:
        dnac.network_settings.create_device_credentials(settings=s, site_id=site)
    except ApiError as err:
        console.print (f"[blink bold red] ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    else:
        time.sleep(5)
        console.print(f'[green] [OK]\n')     


# Get network device credentials IDs
def get_network_credentials_ids():
    try:
        out = dnac.network_settings.get_device_credential_details()
    except ApiError as err:
        console.print (f"[blink bold red] ERROR: {err}")
        console.print ("[cyan] ==> Continue")
    else:
        console.print(f'[green] [OK]\n')

    return out["cli"][0]["id"], out["snmp_v2_write"][0]["id"], out["snmp_v2_read"][0]["id"]


# Get network device credentials IDs
def dump_ids(fabric, cred_cli, cred_rw, cred_ro):
    s = {
            "Fabric ID": fabric,
            "Credentials":  {
                "cli": cred_cli,
                "snmp_rw" : cred_rw,
                "snmp_ro": cred_ro
            }
        }
    
    print(yaml.dump(s, sort_keys=False))
    with open ('dnac_ids.yaml', 'w') as f:
        yaml.dump(s, f, sort_keys=False)
    console.print("[yellow] Dumped DNAC IDs to dnac_ids.yaml")


def ask(step, msg): 
    try: 
        while (Confirm.ask(f"\n[green reverse][{step}/{steps}] [red]{msg} Type y to continue or CTRL+C to exit") == False):
            continue
    except:
        print("\nExiting")
        exit(1)


### Here we came at last ###

if __name__ == "__main__":

    steps = 10
    console.print(f"\n[reverse green] DNAC Site script starting {'(non-config)' if apply_settings==False else ''}")

    # Process input data
    console.print(f"[bold yellow] Parse input data...")
    pod = parse_input(sys.argv)

    # Create API object
    ask (1, "Proceed to API object creation?")
    console.print("\n[bold yellow] Creating API object...")
    dnac = get_connected(pod)

    # Create sites
    if (apply_settings):
        ask (2, "Proceed to create sites?")
        files = "sites/*.json"
        create_sites_from_files(files)

    # Get building site ID for fabric
    ask (3, "Proceed to retrieve fabric site ID?")
    fabric_site_name = "Global/Poland/Warszawa/Hector"
    console.print(f"[bold yellow] Get site {fabric_site_name} info...", end="")
    site = get_site_info(fabric_site_name)
    fabric_site_id = site.response[0].id
    console.print (f"[yellow] Fabric site ID: {fabric_site_id}\n")
    
    # Create global IP pools
    if (apply_settings):    
        ask (4, "Proceed to create global IP pools?")
        globalIpPoolUnderlay, globalIpPoolOverlay, globalIpPoolOverlay6 = setup_data(pod)
        console.print(f"[bold yellow] Create global pools...", end="")
        globalIpPools = {
            "ippool": [ globalIpPoolUnderlay, globalIpPoolOverlay, globalIpPoolOverlay6
            ]
        }
        create_global_pools(globalIpPools)

    # Display global IP pools
    ask (5, "Proceed to display a table od IP pools?")
    console.print(f"[bold yellow] Get global pools...", end="")
    global_pools = get_global_pools().response
    display_global_pools(global_pools)

    # Reserve pools at site
    if (apply_settings):    
        ask (6, "Proceed to reserve site IP pools?")
        console.print(f"[bold yellow] Reserve pools at site {fabric_site_name}...")
        reserve_pool("131", pod, globalIpPoolOverlay, globalIpPoolOverlay6, fabric_site_id)
        reserve_pool("132", pod, globalIpPoolOverlay, globalIpPoolOverlay6, fabric_site_id)
        reserve_pool("133", pod, globalIpPoolOverlay, globalIpPoolOverlay6, fabric_site_id)

    # Create network settings for a site
    if (apply_settings):        
        ask (7, "Proceed to create network settings for fabric site?")
        console.print(f"[bold yellow] Create network settings for site {fabric_site_name}...")
        create_network_settings(fabric_site_id)

    # Create network credentials
    if (apply_settings):        
        ask (8, "Proceed to create network device credentials?")
        console.print(f"[bold yellow] Create network credentials...")
        create_network_credentials(pod)

    # Get credential IDs
    ask (9, "Proceed to retrieve network device credential IDs?")
    console.print(f"[yellow] Get network credentials IDs...")
    credentials_cli_id, credentials_snmp_rw_id, credentials_snmp_ro_id = get_network_credentials_ids()
    console.print(f"CLI: {credentials_cli_id}, SNMP_RW: {credentials_snmp_rw_id}, SNMP_RO: {credentials_snmp_ro_id}")

    # Dump IDs as YAML
    ask (10, "Proceed to dump IDs as YAML?")
    console.print(f"[bold yellow] Dumping object IDs as YAML...")
    dump_ids (fabric_site_id, credentials_cli_id, credentials_snmp_rw_id, credentials_snmp_ro_id)

    console.print("\n[reverse green] DNAC Site script finished\n")
