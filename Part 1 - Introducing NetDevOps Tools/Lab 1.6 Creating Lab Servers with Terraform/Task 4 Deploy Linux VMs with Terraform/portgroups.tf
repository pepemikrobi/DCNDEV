resource "vsphere_host_port_group" "oob_mgmt" {

    name                = format("(110%s) DCLAB_OOB_10%s", var.pod, var.pod)
    host_system_id      = data.vsphere_host.esxi_host.id
    virtual_switch_name = "vSwitch0"

    vlan_id = format("110%s", var.pod)
    allow_promiscuous = true
    allow_forged_transmits = true
    allow_mac_changes = true
}

resource "vsphere_host_port_group" "srv11" {

    name                = format("(1%s11) DCLAB_SRV_11", var.pod)
    host_system_id      = data.vsphere_host.esxi_host.id
    virtual_switch_name = "vSwitch1"

    vlan_id = format("1%s11", var.pod)
    allow_promiscuous = true
    allow_forged_transmits = true
    allow_mac_changes = true
}

resource "vsphere_host_port_group" "srv12" {

    name                = format("(1%s12) DCLAB_SRV_12", var.pod)
    host_system_id      = data.vsphere_host.esxi_host.id
    virtual_switch_name = "vSwitch1"

    vlan_id = format("1%s12", var.pod)
    allow_promiscuous = true
    allow_forged_transmits = true
    allow_mac_changes = true
}

data "vsphere_network" "oob_mgmt" {
    name          = format("(110%s) DCLAB_OOB_10%s", var.pod, var.pod)
    datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_network" "srv11" {
    name          = format("(1%s11) DCLAB_SRV_11", var.pod)
    datacenter_id = data.vsphere_datacenter.datacenter.id
}

data "vsphere_network" "srv12" {
    name          = format("(1%s12) DCLAB_SRV_12", var.pod)
    datacenter_id = data.vsphere_datacenter.datacenter.id
}
