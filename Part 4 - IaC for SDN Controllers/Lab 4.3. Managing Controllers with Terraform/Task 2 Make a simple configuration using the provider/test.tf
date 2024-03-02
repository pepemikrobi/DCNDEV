resource "dnacenter_area" "gdansk" {
    provider = dnacenter

    parameters {

        site {
            area {
                name = "Gdansk"
                parent_name = "Global/Poland"
            }
        }
        type = "area"
    }
}

output "area" {
    value = dnacenter_area.gdansk
}
