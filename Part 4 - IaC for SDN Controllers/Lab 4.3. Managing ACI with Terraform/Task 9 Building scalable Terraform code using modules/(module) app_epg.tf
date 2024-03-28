resource "aci_application_profile" "APPs" {
    name = var.app_name
    tenant_dn = var.tenant_id
}

resource "aci_application_epg" "EPGs" {
    name = var.epg_name
    application_profile_dn = aci_application_profile.APPs.id
    relation_fv_rs_bd = var.bd_id
}
