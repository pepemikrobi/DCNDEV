catc_username = "admin"
catc_url = "https://podX-dnac.sdn.lab"

test_site_parent_name = "Global/Poland/Warszawa"
test_site_name = "Corp"

# VN definitions
global_ip_pool_name = "PODX_POOL_OVERLAY"

virtual_networks = {
    "VN_A" = { 
        anycast_gw = "10.1X.150.1/24" 
    }
    "VN_B" = { 
        anycast_gw = "10.1X.151.1/24", 
        l2_flooding_enabled = true
    }
    "VN_C" = { 
        anycast_gw = "10.1X.152.1/24", 
        l2_flooding_enabled = true,
        wireless_pool = true 
    }
}
