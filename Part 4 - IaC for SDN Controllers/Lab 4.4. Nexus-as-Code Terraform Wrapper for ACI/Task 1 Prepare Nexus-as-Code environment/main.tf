terraform {
    required_providers {
        aci = {
        source = "CiscoDevNet/aci"
        }
    }
    backend "http" {
    }
}

provider "aci" {
    username = var.aci_username
    password = var.aci_password
    url      = var.aci_url
    insecure = true
}

module "aci" {
    source  = "netascode/nac-aci/aci"

    yaml_directories = ["data"]
    manage_tenants = true
}
