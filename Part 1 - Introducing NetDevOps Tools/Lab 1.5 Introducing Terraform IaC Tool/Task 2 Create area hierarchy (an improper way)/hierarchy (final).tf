resource "dnacenter_area" "pod5" {
    provider = dnacenter
    parameters {
        site {
            area {
            name        = "POD5"
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
            parent_name = "POD5"
            }
        }
        type = "area"
    }
}

resource "dnacenter_area" "poland" {
    provider = dnacenter
    parameters {
        site {
            area {
            name        = "Poland"
            parent_name = "Global/Europe"
            }
        }
    type = "area"
    }
}
