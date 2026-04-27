resource "dnacenter_area" "podX" {
    provider = dnacenter
    parameters {
        site {
            area {
            name        = "PODX"
            parent_name = "Global"
            }
        }
        type = "area"
    }
}

resource "dnacenter_area" "europe" {
    provider = dnacenter
    parameters {
        site {
            area {
            name        = "Europe"
            parent_name = "Global/PODX"
            }
        }
        type = "area"
    }
    depends_on = [ dnacenter_area.podX ]
}

resource "dnacenter_area" "poland" {
    provider = dnacenter
    parameters {
        site {
            area {
            name        = "Poland"
            parent_name = "Global/PODX/Europe"
            }
        }
    type = "area"
    }
    depends_on = [ dnacenter_area.europe ]
}

resource "dnacenter_building" "hector" {
    provider = dnacenter
    parameters {
        site {
            building {
            address     = "Gwiaździsta 19, 01-651 Warszawa"
            name        = "Hector"
            parent_name = "Global/PODX/Europe/Poland"
            }
        }
    type    = "building"
    }
    depends_on = [ dnacenter_area.poland ]
}

