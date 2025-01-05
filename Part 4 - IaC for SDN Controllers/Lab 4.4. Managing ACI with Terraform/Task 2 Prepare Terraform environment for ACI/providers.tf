terraform {
    required_providers {
        aci = {
        source  = "CiscoDevNet/aci"
        }
    }
}

provider "aci" {
    username = var.aci_username
    password = var.aci_password
    url      = var.aci_url
    insecure = true
}
