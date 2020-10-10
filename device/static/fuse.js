let fuse_url = "http://" + ip_address + ":" + port + "/fuses";

fetch(fuse_url)
    .then((resp) => resp.json())
    .then(function (data) {
        var table = document.getElementById("fuse_table");
        var first_row = table.insertRow(0);
        var corner_cell = first_row.insertCell(0);
        corner_cell.innerHTML = "Fuses:&nbsp;";
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
                switch (data[chip][i]) {
                    case "fired":
                        cell.style = "background-color:" + blue;
                        break;
                    case "fireing":
                        cell.style = "background-color:" + yellow;
                        break;
                    case "staged":
                        cell.style = "background-color:" + green;
                        break;
                    case "none":
                        cell.style = "background-color:" + grey;
                        break;
                    default:
                        cell.style = "background-color:" + red;
                }
            }
        }
    })
    .catch(function (error) {
        console.log(error);
        var table = document.getElementById("fuse_table");
        var row = table.insertRow(0);
        var cell = row.insertCell(0);
        cell.innerHTML = "COULD NOT LOAD FUSE STATES!"
    })