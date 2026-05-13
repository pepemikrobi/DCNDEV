module "catc_test_fabric_corp" {
    source = "./modules/catc_fabric"
    test_site_parent_name = var.test_site_parent_name
    test_site_name = var.test_site_name
    global_ip_pool_name = var.global_ip_pool_name
    virtual_networks = var.virtual_networks
} 
