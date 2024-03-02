terraform {
    required_providers {
        dnacenter = {
            source = "cisco-en-programmability/dnacenter"
        }
    }
}

provider "dnacenter" {
    username = "admin"
    password = "AdmeenXsisko"
    base_url = "https://podX-dnac.sdn.lab"
    ssl_verify = "false"
}
