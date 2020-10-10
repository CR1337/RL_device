let lock_url = "http://" + ip_address + ":" + port + "/lock";

fetch(lock_url)
    .then((resp) => resp.json())
    .then(function (data) {
        document.getElementById("locked").innerHTML = data.locked;
    })
    .catch(function (error) {
        console.log(error);
        document.getElementById("locked").innerHTML = "COULD NOT LOAD LOCK STATE!";
    })