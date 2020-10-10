let config_url = "http://" + ip_address + ":" + port + "/config";

fetch(config_url)
    .then((resp) => resp.json())
    .then(function (data) {
        var table = document.getElementById("config_table");
        var row_idx = 0;
        first_row = table.insertRow(row_idx);
        first_cell = first_row.insertCell(0);
        first_cell.innerHTML = "Config:"
        first_cell.style.fontWeight = "bold";
        row_idx++;

        for (category in data) {
            category_row = table.insertRow(row_idx);
            category_cell = category_row.insertCell(0);
            category_cell.innerHTML = category
            category_cell.style.fontWeight = "bold";
            row_idx++;

            for (key in data[category]) {
                row = table.insertRow(row_idx);
                key_cell = row.insertCell(0);
                value_cell = row.insertCell(1);
                key_cell.innerHTML = key;
                value = data[category][key];
                if ( typeof value === "object" ) {
                    value = JSON.stringify(value);
                }
                value_cell.innerHTML = value;
                row_idx++;
            }
        }
    })
    .catch(function (error) {

    })