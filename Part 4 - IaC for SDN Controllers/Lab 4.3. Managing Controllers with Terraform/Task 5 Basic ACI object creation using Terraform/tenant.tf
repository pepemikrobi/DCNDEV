resource "aci_tenant" "PODX_Tenant1" {
    name = "podX_tenant1"
}

resource "aci_vrf" "VRF1" {
    name = "VRF1"
    tenant_dn = aci_tenant.PODX_Tenant1.id
}

resource "aci_vrf" "VRF2" {
    name = "VRF2"
    tenant_dn = aci_tenant.PODX_Tenant1.id
}

resource "aci_bridge_domain" "BD1" {
    name = "BD1"
    tenant_dn = aci_tenant.PODX_Tenant1.id
    relation_fv_rs_ctx = aci_vrf.VRF1.id
}

resource "aci_bridge_domain" "BD2" {
    name = "BD2"
    tenant_dn = aci_tenant.PODX_Tenant1.id
    relation_fv_rs_ctx = aci_vrf.VRF2.id
}

resource "aci_application_profile" "APP1" {
    name = "APP1"
    tenant_dn = aci_tenant.PODX_Tenant1.id
}

resource "aci_application_epg" "EPG1" {
    name = "EPG1"
    application_profile_dn = aci_application_profile.APP1.id
    relation_fv_rs_bd = aci_bridge_domain.BD1.id
}

resource "aci_application_epg" "EPG2" {
    name = "EPG2"
    application_profile_dn = aci_application_profile.APP1.id
    relation_fv_rs_bd = aci_bridge_domain.BD2.id
}
