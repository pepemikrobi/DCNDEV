variable "catc_username" {
    type = string
}

variable "catc_password" {
    type      = string
    sensitive = true
}

variable "catc_url" {
    type = string
}
