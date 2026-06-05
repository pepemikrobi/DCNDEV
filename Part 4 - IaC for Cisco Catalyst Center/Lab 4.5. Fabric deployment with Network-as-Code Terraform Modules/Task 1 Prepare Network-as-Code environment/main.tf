module "nac" {
    source  = "netascode/nac-catalystcenter/catalystcenter"
    version = "0.4.2"

    yaml_directories = ["data/"]
}

terraform {
    required_providers {
        catalystcenter = {
            source  = "CiscoDevNet/catalystcenter"
            version = "~> 0.5.11"
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
