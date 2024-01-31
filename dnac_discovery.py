# DNA Center SDK example for discovering devices
# A part of Developing with Cisco Networks DevOps Style (DCNDEV) Course
# Inspired by https://github.com/CiscoDevNet/startnow-dnac-sdk
# Author: robert.slaski@gmail.com

from datetime import datetime
import time
import sys
import yaml
from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from dnacentersdk import DNACenterAPI
from dnacentersdk.exceptions import ApiError, AccessTokenError

console = Console()
table = Table(show_header=True, header_style="bold green")
global dnac1
global steps
apply_settings = True

# A header option for synchronous API run
SYNC =  { "__runsync" : True }

# Parse command-line input data
def parse_input(argv):
    # Retrieve pod argument
    if len(argv) != 2:
        print ("""Usage:
        dnac_discovery.py <pod_number> 
    
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


# Get network device credentials IDs
def read_ids(filename):

    with open (filename, 'r') as f:
        yaml_data = yaml.safe_load(f)
    console.print(f"[yellow] Loaded DNAC IDs from {filename}")
    try:
        data = yaml_data['Fabric ID'], yaml_data['Credentials']['cli'], yaml_data['Credentials']['snmp_rw'], yaml_data['Credentials']['snmp_ro']
    except KeyError: 
        console.print("[red] There was a problem reading YAML data structure, exiting.")
        exit(1)
    else:
        return data


def initialize_discovery(devices, credentials):
    discovery_name = f'Discovery-{time.strftime("%Y%m%d_%H%M%S", time.localtime())}'
    console.print(f"[yellow] Initializing discovery [yellow bold]{discovery_name}")

    discovery = dnac.discovery.start_discovery(
        discoveryType="Range", preferredMgmtIPMethod="UseLoopBack", ipAddressList=devices,
        protocolOrder="ssh", globalCredentialIdList=credentials, name=discovery_name)
    
    task_details = dnac.task.get_task_by_id(discovery.response.taskId)
    task_progress = task_details.response.progress
    console.print(f"[yellow] Discovery initialized at {datetime.fromtimestamp(int(task_details['response']['startTime'])/1000)}, TaskID [yellow bold]{discovery.response.taskId}")

    with console.status("[bold green]Kicking off Auto-Discovery...") as status:
        time.sleep(3)
        while task_progress == "Inventory service initiating discovery.":
            task_progress = dnac.task.get_task_by_id(discovery.response.taskId).response.progress


def get_discovery_status():
    console.print("[bold yellow] Discovery initiated, checking progress...")
    disco = dnac.discovery.get_discoveries_by_range(records_to_return=1,start_index=1)
    disco_id = disco.response[0].id 
    console.print (f'[yellow] Discovery ID: {disco_id}')
    disco_status = disco.response[0].discoveryStatus
    with console.status("[yellow] Discovering Devices {}...".format(disco_status)) as status:
        while disco_status == "Active":
            disco_status= dnac.discovery.get_discoveries_by_range(records_to_return=1, start_index=1).response[0].discoveryStatus
            console.print(f"[yellow] Checking, status {disco_status}...")
            time.sleep(2)
    console.print(f"[yellow] Discovery {disco_id} completed, status {disco_status}")
    disco_returned = dnac.discovery.get_discovery_by_id(id=disco_id)
    return disco_returned.response


def save_discovered_devices(devices_list):
    print (f'Discovered devices ID list: {devices_list}')
    s = { "Discovered devices": devices_list }
    
    #print(yaml.dump(s, sort_keys=False))
    with open ('dnac_discovered_devices.yaml', 'w') as f:
        yaml.dump(s, f, sort_keys=False)
    console.print("[yellow] Dumped discovered device IDs to dnac_discovered_devices.yaml")


def retrieve_device_details():
    console.print("[yellow] Reading device IDs from YAML file...")
    with open('dnac_discovered_devices.yaml', 'r') as f:
        console.print(f'[green] [OK]')
        yaml_data = yaml.safe_load(f)
        try: 
            device_id_list = yaml_data['Discovered devices']
        except KeyError: 
            console.print("[red] There was a problem reading YAML data structure, exiting.")
            exit(1)

    table.add_column("Hostname")
    table.add_column("MacAdd")
    table.add_column("Serial Number")
    table.add_column("Software Type")
    table.add_column("type")
    table.add_column("IP Address")
    table.add_column("Family")
    table.add_column("Device")

    for device in device_id_list:
        device = dnac.devices.get_device_by_id(id=device)
        table.add_row(
          device.response.hostname,
          device.response.macAddress,
          device.response.serialNumber,
          device.response.softwareType,
          device.response.type,
          device.response.managementIpAddress,
          device.response.family,
          device.response.platformId
        )
    console.print(table)

    return device_id_list


def assign_device_to_site(device_list, fabric_site_id):

    device_ip_structure = []
    try:
        site_name = dnac.sites.get_site(site_id=fabric_site_id).response.siteNameHierarchy
    except ApiError as err:
        console.print(f'[blink bold red] Retrieving site API error: {err}')
        exit (1)

    console.print(f'[yellow] Assigning devices to site ID [bold]{fabric_site_id}[/bold], name [bold]{site_name}[/bold]')

    for device_id in device_list:
        device = dnac.devices.get_device_by_id(id=device_id).response
        console.print(f'[yellow] Assign discovered device [bold]{device_id}[/bold], hostname [bold]{device.hostname}[/bold], IP [bold]{device.managementIpAddress}[/bold] to the site')
        device_ip_structure.append({"ip": device.managementIpAddress})
    try:
        info = dnac.sites.assign_devices_to_site(device = device_ip_structure, site_id=fabric_site_id, headers=SYNC)
    except ApiError as err:
        console.print(f'[blink bold red] Assign device to site API error: {err}')
        console.print ("[cyan] ==> Continue")
    except TypeError as err:
        console.print(f'[blink bold red] Assign device to site type error: {err}')
    else:
        print (f'Assigned info: {info}')


def ask(step, msg): 
    try: 
        while (Confirm.ask(f"\n[green reverse][{step}/{steps}] [red]{msg} Type y to continue or CTRL+C to exit") == False):
            continue
    except:
        print("\nExiting")
        exit(1)


### Here we came at last ###

if __name__ == "__main__":

    steps = 6
    console.print(f"\n[reverse green] DNAC discovery script starting {'(non-config)' if apply_settings==False else ''}")

    # Process input data
    console.print(f"[bold yellow] Parse input data...")
    pod = parse_input(sys.argv)

    # Create API object
    ask (1, "Proceed to API object creation?")
    console.print("\n[bold yellow] Creating API object...")
    dnac = get_connected(pod)

    # Read IDs from YAML file
    filename = 'dnac_ids.yaml'
    ask (2, f"Proceed to read fabric and credential IDs from YAML file {filename}?")
    console.print(f"[bold yellow] Reading object IDs from YAML file {filename}...")
    fabric_site_id, credentials_cli_id, credentials_snmp_rw_id, credentials_snmp_ro_id = read_ids(filename)
    console.print (f" Fabric site ID: {fabric_site_id}, CLI ID: {credentials_cli_id}, SNMP RW ID: {credentials_snmp_rw_id}, SNMP RO ID: {credentials_snmp_ro_id}")
    
    # Initiate discovery and check status
    if (apply_settings):
        ask (3, f"Proceed to initialize device discovery?")
        console.print(f"[bold yellow] Initializing device discovery...")
        initialize_discovery(f"10.1{pod}.127.3-10.1{pod}.127.102", [credentials_cli_id, credentials_snmp_rw_id, credentials_snmp_ro_id])
        console.print(f"[bold yellow] Initializing device discovery...")
        disco_response = get_discovery_status()
        print (disco_response)
        if (disco_response.deviceIds == " "):
            console.print("[bold yellow] No devices discovered, exiting")
            exit (0)
        else:
            devices_list = disco_response.deviceIds.split(",")
            console.print(f"[bold yellow] {len(devices_list)} devices discovered")

    # Save discovered device IPs
    if (apply_settings):
        ask (4, f"Proceed to save discovered device IPs?")
        console.print(f"[yellow] Save discovered device IPs...")
        save_discovered_devices(devices_list)
    
    # Load device IPs and retrieve device details
    ask (5, f"Proceed to retrieving discovered device details?")
    console.print(f"[yellow] Get discovered device details...")
    devices = retrieve_device_details()

    # Add devices to site
    if (apply_settings):
        ask (6, f"Proceed to add discovered devices to fabric site?")
        console.print(f"[yellow] Add discovered devices to site...")
        assign_device_to_site(devices, fabric_site_id)
    
    console.print("\n[reverse green] DNAC Discovery script finished\n")
