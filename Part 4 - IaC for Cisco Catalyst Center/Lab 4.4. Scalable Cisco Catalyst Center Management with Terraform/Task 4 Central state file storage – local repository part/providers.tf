terraform {
    required_providers {
        catalystcenter = {
            source = "CiscoDevNet/catalystcenter"
        }
    }
    backend "http" {
    }  
}

provider "catalystcenter" {
    username = var.catc_username
    password = var.catc_password
    url      = var.catc_url
}


