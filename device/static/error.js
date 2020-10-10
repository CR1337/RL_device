let error_url = "http://" + ip_address + ":" + port + "/error";

fetch(error_url)
    .then((resp) => resp.json())
    .then(function (data) {
        var table = document.getElementById("error_table");
        var first_row = table.insertRow(0);
        var corner_cell = first_row.insertCell(0);
        corner_cell.innerHTML = "Errors:";
        corner_cell.style.fontWeight = "bold";
        for (i = 0; i <= 15; i++) {
            var cell = first_row.insertCell(i + 1);
            cell.innerHTML = i;
            cell.style.fontWeight = "bold";
        }

        var chip_idx = -1;
        for (chip in data) {
            chip_idx++;
            var row = table.insertRow(chip_idx + 1);
            var first_cell = row.insertCell(0);
            first_cell.innerHTML = chip.toUpperCase();
            first_cell.style.fontWeight = "bold";
            for (i = 0; i <= 15; i++) {
                var cell = row.insertCell(i + 1);
                cell.innerHTML = "&nbsp;&nbsp;";
                if (data[chip][i]) {
                    cell.style = "background-color:" + red;
                } else {
                    cell.style = "background-color:" + green;
                }
            }
        }
    })
    .catch(function (error) {
        console.log(error);
        var table = document.getElementById("error_table");
        var row = table.insertRow(0);
        var cell = row.insertCell(0);
        cell.innerHTML = "COULD NOT LOAD ERROR STATES!"
    })
