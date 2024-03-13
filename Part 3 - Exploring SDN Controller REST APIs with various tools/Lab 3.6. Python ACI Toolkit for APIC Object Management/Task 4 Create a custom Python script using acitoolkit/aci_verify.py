import json
from sys import exit
from acitoolkit.acitoolkit import Session, Tenant, Context, BridgeDomain, Subnet

# APIC Credentials
APIC_HOST = "https://apic1.sdn.lab"
APIC_USERNAME = "podX"
APIC_PASSWORD = "AdminXsisko$"

def as_dict(object_list):
    # Helper function to create a name-indexed dictionary 
    # from a list of objects returned by acitoolkit get functions 
    objects_dict = {} 
    for obj in object_list: 
        objects_dict[obj.name] = obj 
    return objects_dict

tenant_name = "PODX"
vrf_name = "VRF1"
bridge_domain_name = "BD1"

session = Session(APIC_HOST, APIC_USERNAME, APIC_PASSWORD)
session.login()

tenants = as_dict(Tenant.get(session))

print(f'All tenants: {tenants.keys()}')

if tenants.get(tenant_name) is None:
    print(f'Couldn\'t find tenant {tenant_name} on the APIC.') 
    exit(1)

tenant = tenants.get(tenant_name)
print(f'Tenant {tenant.name} exists with DN {tenant.dn}!')

vrfs = as_dict(Context.get(session, tenant))

if vrf_name in vrfs:
    print(f'{vrf_name} exists with DN {vrfs[vrf_name].dn}.') 
else:
    print(f'Couldn\'t find VRF {vrf_name} under tenant {tenant.name}.')

bridge_domains = as_dict(BridgeDomain.get(session, tenant))
if bridge_domain_name in bridge_domains:
    bd = bridge_domains[bridge_domain_name] 
    print(f'{bd.name} exists with DN {bd.dn}.') 
    print('It has the following subnets:') 

    for subnet in Subnet.get(session, bd, tenant): 
        print(subnet.get_addr()) 
else:
    print(f'Couldn\'t find BD {bridge_domain_name} under tenant {tenant.name}.')  

