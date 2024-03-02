resource "dnacenter_area" "europe" {
    provider = dnacenter
    parameters {
        site {
            area {
            name        = "Europe"
            parent_name = "Global"
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
