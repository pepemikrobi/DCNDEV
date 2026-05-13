# Look up all global IP pools to resolve the configured pool name to its ID
data "catalystcenter_ip_pools" "all" {}

locals {
    global_ip_pool_id = one([
        for pool in data.catalystcenter_ip_pools.all.pools : pool.id
        if pool.name == var.global_ip_pool_name
    ])
}

# Reserve a subnet per VN at the Corp site
resource "catalystcenter_ip_pool_reservation" "vn" {
    for_each            = var.virtual_networks
    name                = each.key
    pool_type           = "Generic"
    site_id             = catalystcenter_building.test_site.id
    ipv4_global_pool_id = local.global_ip_pool_id
    ipv4_subnet         = cidrhost(each.value.anycast_gw, 0)
    ipv4_prefix_length  = tonumber(split("/", each.value.anycast_gw)[1])
    ipv4_gateway        = split("/", each.value.anycast_gw)[0]
}

# Create L3 Virtual Networks and assign them to the fabric site
resource "catalystcenter_fabric_l3_virtual_network" "vn" {
    for_each             = var.virtual_networks
    virtual_network_name = each.key
    fabric_ids           = [catalystcenter_fabric_site.test_site.id]
}

# Create an anycast gateway for each VN
resource "catalystcenter_anycast_gateway" "vn" {
    for_each                     = var.virtual_networks
    fabric_id                    = catalystcenter_fabric_site.test_site.id
    virtual_network_name         = catalystcenter_fabric_l3_virtual_network.vn[each.key].virtual_network_name
    ip_pool_name                 = catalystcenter_ip_pool_reservation.vn[each.key].name
    traffic_type                 = "DATA"
    critical_pool                = false
    l2_flooding_enabled          = each.value.l2_flooding_enabled
    wireless_pool                = each.value.wireless_pool
    ip_directed_broadcast        = false
    intra_subnet_routing_enabled = false
    multiple_ip_to_mac_addresses = false
    auto_generate_vlan_name      = true
}
