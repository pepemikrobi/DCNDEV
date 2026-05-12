resource "aci_application_profile" "APPs" {
    name = var.app_name
    tenant_dn = var.tenant_id
}

resource "aci_application_epg" "EPGs" {
    name = var.epg_name
    application_profile_dn = aci_application_profile.APPs.id
    relation_fv_rs_bd = var.bd_id
}

resource "aci_epg_to_domain" "EPG_Domain" {
    tdn = var.domain_name
    application_epg_dn = aci_application_epg.EPGs.id
}

resource "aci_epg_to_static_path" "EPG_Paths" {
    for_each = toset (var.interfaces)
    tdn = each.key
    encap = format("vlan-%s",var.vlan_id)
    application_epg_dn = aci_application_epg.EPGs.id
} 
