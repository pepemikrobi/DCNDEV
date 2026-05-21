terraform {
    required_providers {
        catalystcenter = {
            source = "CiscoDevNet/catalystcenter"
        }
    }
}

provider "catalystcenter" {
    username = var.catc_username
    password = var.catc_password
    url      = var.catc_url
}