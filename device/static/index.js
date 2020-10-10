var ip_address = location.hostname;
var port = "";
const metas = document.getElementsByTagName("meta");
for (let i = 0; i < metas.length; i++) {
    if (metas[i].getAttribute('name') === "port") {
        port = metas[i].getAttribute('content');
    }
}

const red = "#ff0000";
const green = "#00ff00";
const blue = "#0000ff";
const yellow = "#ffff00";
const grey = "#aaaaaa";