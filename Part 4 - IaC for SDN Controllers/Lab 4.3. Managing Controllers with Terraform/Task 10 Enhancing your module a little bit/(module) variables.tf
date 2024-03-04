variable "tenant_id" {
    type = string
    description = "ACI Tenant DN"
}

variable "bd_id" {
    type = string
    description = "ACI Bridge Domain DN"
}

variable "app_name" {
    type = string
    description = "ACI Application Profile DN"
}

variable "epg_name" {
    type = string
    description = "ACI EPG DN"
}

variable "domain_name" {
    type = string
    description = "ACI Domain DN"
}

variable "vlan_id" {
    type = string
    description = "VLAN ID for EPG to Domain association"
}

variable "interfaces" {
    type = list(string)
    description = "Interface list for EPG to Domain association"
}
