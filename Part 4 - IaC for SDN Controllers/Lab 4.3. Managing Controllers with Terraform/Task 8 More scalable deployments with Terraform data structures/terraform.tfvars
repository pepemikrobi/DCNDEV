aci_username = "podX"
aci_url = "https://apic1.sdn.lab"

vrfs = {
    "VRF1" = {
        tenant = "podX_tenant1"
    }
    "VRF2" = {
        tenant = "podX_tenant1"
    }
}

bridge_domains = {
    "BD1" = {
        vrf = "VRF1"
        subnet = "10.101.1.254/24"
    }
    "BD2" = {
        vrf = "VRF1"
        subnet = "10.101.2.254/24"
    }
    "BD3" = {
        vrf = "VRF2"
        subnet = "10.102.3.254/24"
    }
}