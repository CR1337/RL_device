let program_state_url = "http://" + ip_address + ":" + port + "/program/state";

fetch(program_state_url)
    .then((resp) => resp.json())
    .then(function (data) {
        document.getElementById("program_state").innerHTML = data.state;
    })
    .catch(function (error) {
        console.log(error);
        document.getElementById("program_state").innerHTML = "COULD NOT LOAD PROGRAM STATE!";
    })