resource "aci_tenant" "PODX_Tenant1" {
    name = "podX_tenant1"
}

# resource "aci_vrf" "VRF1" {
#     name = "VRF1"
#     tenant_dn = aci_tenant.PODX_Tenant1.id
# }

# resource "aci_vrf" "VRF2" {
#     name = "VRF2"
#     tenant_dn = aci_tenant.PODX_Tenant1.id
# }

resource "aci_vrf" "VRFs" {
    for_each = var.vrfs
    name = each.key
    tenant_dn = aci_tenant.PODX_Tenant1.id
}

# resource "aci_bridge_domain" "BD1" {
#     name = "BD1"
#     tenant_dn = aci_tenant.PODX_Tenant1.id
#     relation_fv_rs_ctx = aci_vrf.VRF1.id
# }

# resource "aci_bridge_domain" "BD2" {
#     name = "BD2"
#     tenant_dn = aci_tenant.PODX_Tenant1.id
#     relation_fv_rs_ctx = aci_vrf.VRF2.id
# }

resource "aci_bridge_domain" "BDs" {
    for_each = var.bridge_domains
    name = each.key
    tenant_dn = aci_tenant.PODX_Tenant1.id
    relation_fv_rs_ctx = aci_vrf.VRFs[each.value.vrf].id
}

resource "aci_subnet" "Subnets" {
    for_each = var.bridge_domains
    parent_dn = aci_bridge_domain.BDs[each.key].id
    ip = each.value.subnet
    scope = ["public"]
}

resource "aci_application_profile" "APP1" {
    name = "APP1"
    tenant_dn = aci_tenant.PODX_Tenant1.id
}

resource "aci_application_epg" "EPG1" {
    name = "EPG1"
    application_profile_dn = aci_application_profile.APP1.id
    relation_fv_rs_bd = aci_bridge_domain.BDs["BD1"].id
}

resource "aci_application_epg" "EPG2" {
    name = "EPG2"
    application_profile_dn = aci_application_profile.APP1.id
    relation_fv_rs_bd = aci_bridge_domain.BDs["BD2"].id
}

module "APP1_EPG1" {
    source = "./modules/app_epg"
    tenant_id = aci_tenant.PODX_Tenant1.id
    app_name = "APP1"
    epg_name = "EPG1"
    bd_id = aci_bridge_domain.BDs["BD1"].id
} 

module "APP1_EPG2" {
    source = "./modules/app_epg"
    tenant_id = aci_tenant.PODX_Tenant1.id
    app_name = "APP1"
    epg_name = "EPG2"
    bd_id = aci_bridge_domain.BDs["BD2"].id
}

