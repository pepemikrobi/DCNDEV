terraform {
    required_providers {
        dnacenter = {
        source = "cisco-en-programmability/dnacenter"
        }
    }
    backend "http" {
    }
}

provider "dnacenter" {
    username = var.dnac_username
    password = var.dnac_password
    base_url = var.dnac_url
    ssl_verify = "false"
}
