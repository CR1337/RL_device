let environment_url = "http://" + ip_address + ":" + port + "/environment";

fetch(environment_url)
    .then((resp) => resp.json())
    .then(function (data) {
        var table = document.getElementById("environment_table");
        var row_idx = 0;
        first_row = table.insertRow(row_idx);
        first_cell = first_row.insertCell(0);
        first_cell.innerHTML = "Environment:"
        first_cell.style.fontWeight = "bold";
        row_idx++;

        for (key in data) {
            row = table.insertRow(row_idx);
            key_cell = row.insertCell(0);
            value_cell = row.insertCell(1);
            key_cell.innerHTML = key;
            value = data[key];
            value_cell.innerHTML = value;
            row_idx++;
        }
    })
    .catch(function (error) {

    })