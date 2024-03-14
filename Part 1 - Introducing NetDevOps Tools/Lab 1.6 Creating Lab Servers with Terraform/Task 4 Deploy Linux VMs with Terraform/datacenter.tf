data "vsphere_datacenter" "datacenter" {
    name = "PODS"
}

data "vsphere_host" "esxi_host" {
    name          = var.esxi_hostname
    datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_resource_pool" "pool" {
    name          = format("pod%s_dcndev", var.pod)
    datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_datastore" "datastore" {
    name          = var.esxi_datastore
    datacenter_id = data.vsphere_datacenter.datacenter.id
}
