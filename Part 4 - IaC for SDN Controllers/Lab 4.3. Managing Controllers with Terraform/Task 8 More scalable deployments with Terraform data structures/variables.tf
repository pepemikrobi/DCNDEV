variable "aci_username" {
    type = string
}

variable "aci_password" {
    type = string
}

variable "aci_url" {
    type = string
}

variable "vrfs" {
    type = map (
        object(
        {
            tenant = string
        }
        )
    )

    }
    variable "bridge_domains" {
    type = map (
        object(
        {
            vrf = string
            subnet = string
        }
        )
    )
}