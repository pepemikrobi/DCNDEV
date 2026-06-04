variable "catc_username" {
    type = string
}

variable "catc_password" {
    type = string
}

variable "catc_url" {
    type = string
}

variable "test_site_parent_name" {
    type = string
}
variable "test_site_name" {
    type = string
}

variable "global_ip_pool_name" {
    type = string
}

variable "virtual_networks" {
    type = map(object({
        anycast_gw    = string
        l2_flooding_enabled  = optional(bool, false)
        wireless_pool = optional(bool, false)
    }))
    default = {}
}