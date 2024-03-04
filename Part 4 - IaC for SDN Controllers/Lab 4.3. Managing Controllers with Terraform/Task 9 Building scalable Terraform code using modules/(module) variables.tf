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
