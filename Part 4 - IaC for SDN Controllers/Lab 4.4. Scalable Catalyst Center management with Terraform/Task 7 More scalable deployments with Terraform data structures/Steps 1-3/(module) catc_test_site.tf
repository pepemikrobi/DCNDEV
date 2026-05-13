
# Add a test site
data "catalystcenter_site" "test_site_parent" {
    name_hierarchy = var.test_site_parent_name
}

resource "catalystcenter_building" "test_site" {
    name      = var.test_site_name
    country   = "Poland"
    parent_id = data.catalystcenter_site.test_site_parent.id  
    latitude  = 52.23
    longitude = 21
}

# Create a test fabric site and telemetry settings for it
resource "catalystcenter_telemetry_settings" "test_site" {
    site_id                             = catalystcenter_building.test_site.id
    enable_wired_data_collection        = true
    enable_wireless_telemetry           = true
    use_builtin_trap_server             = true
    use_builtin_syslog_server           = true
    netflow_collector                   = "Builtin"
    enable_netflow_collector_on_devices = false
    depends_on                          = [catalystcenter_building.test_site]
}

    resource "catalystcenter_fabric_site" "test_site" {
    site_id                     = catalystcenter_building.test_site.id
    authentication_profile_name = "No Authentication"
    pub_sub_enabled             = true
    depends_on                  = [catalystcenter_telemetry_settings.test_site]
}
