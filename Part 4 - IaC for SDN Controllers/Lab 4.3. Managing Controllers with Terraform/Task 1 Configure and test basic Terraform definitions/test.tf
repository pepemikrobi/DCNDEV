data "dnacenter_device_credential" "test" {
    provider = dnacenter
}

output "cred" {
    value = data.dnacenter_device_credential.test
}
