vcsa_hostname = "vcenter.sdn.lab"
vcsa_username = "podX-admin@hector.lan"
esxi_hostname = "podX-esxY.sdn.lab"
esxi_datastore = "podX-esxY-ds1-new"

pod = X

server_data = {

    SRV11 = {
        name = "podX-srv11"
        index = 18
        ens224 = "srv11"
    }
    SRV12 = {
        name = "podX-srv12"
        index = 19
        ens224 = "srv12"
    }
}
