document.addEventListener("DOMContentLoaded", init);
let host;
let canvas;
let ctx;
let lastUpdate;
let interval;

function init(event) {
    host = "http://" + window.location.hostname + ":" + window.location.port;
    canvas = document.getElementById("canvas");
    ctx = canvas.getContext("2d");
    lastUpdate = new Date().getTime();
    resizeCanvas();
    loadImage();
    interval = setInterval(updateNewPixels, 1000);
}

function updateInterval(func, timeout){
    clearInterval(interval);
    console.log("Setting Interval to", func.name);
    interval = setInterval(func, timeout);
}

function changeCanvasSize(x, y){
    canvas.width = x;
    canvas.height = y;
}

function updateTime(){
    lastUpdate = Math.floor(Date.now() / 1000);
}

function getCanvasSize() {
    return new Promise(function(resolve, reject) {
        let sizeURL = host + "/canvas/size";
        let xhrSize = new XMLHttpRequest();

        xhrSize.open("GET", sizeURL, true);
        xhrSize.onload = function () {
            if (xhrSize.status === 200) {
                let sizeData = JSON.parse(xhrSize.response);
                let sizeX = sizeData.x;
                let sizeY = sizeData.y;
                resolve([sizeX, sizeY]);
            } else {
                console.log("Endpoint " + sizeURL + " statuscode ", xhrSize.status);
                reject("Error with status " + xhrSize.status);
            }
        }

        xhrSize.onerror = function() {
            //console.error("Could not reach endpoint" + sizeURL);
            reject("Couldn't reach endpoint");
        };

        xhrSize.send();
    });
}

function resizeCanvas() {
    getCanvasSize().then(function (size){
        changeCanvasSize(size[0], size[1]);
    }).catch(function (error){
        console.error("Error while getting canvas size!");
    });
}

function loadImage(){

    let imgURL = host + "/canvas/";
    let xhrImg = new XMLHttpRequest();

    xhrImg.open("GET", imgURL, true);
    xhrImg.responseType = "blob";

    xhrImg.onload = function(event) {
        if (xhrImg.status === 200) {
            let blob = xhrImg.response;
            let img = new Image();
            img.onload = function() {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            };
            img.src = URL.createObjectURL(blob);
        } else {
            console.error("Error on loading " + imgURL + ": ", xhrImg.statusText);
            ctx.fillStyle = "black";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
    };

    xhrImg.onerror = function(event) {
        console.error("Error on loading " + imgURL + ": ", xhrImg.statusText);
            ctx.fillStyle = "black";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    xhrImg.send();
    updateTime();
}

function getNewPixels(callback) {
    let url = host + "/canvas/since?timestamp=" + (lastUpdate - 1); // -1 to ensure pixels weren't updated in the meantime
    fetch(url)
        .then(response => {
            if (response.redirected && response.url === host + "/canvas/"){
                loadImage();
                callback([]);
            } else {
                if (response.status === 404){
                    throw "offline";
                }
                response.json().then(r => {
                    callback(r)
                })
            }
        })
        .catch(error => {
            console.log("Error: ", error);
            if (error instanceof TypeError){
                updateInterval(offlineHandler, 6000);
            }
            callback([]);
        });
}

function hexToRgb(hex) {
    if (hex.length === 6) {
        hex = '#' + hex;
    }
    let bigint = parseInt(hex.slice(1), 16);
    let r = (bigint >> 16) & 255;
    let g = (bigint >> 8) & 255;
    let b = bigint & 255;
    return [r, g, b];
}

function changePixel(x, y, color){
    let imgData = ctx.getImageData(x, y, 1, 1);
    let data = imgData.data;

    let [r, g, b] = hexToRgb(color);
    data[0] = r;
    data[1] = g;
    data[2] = b;
    ctx.putImageData(imgData, x, y);
}

function updateNewPixels() {

    getNewPixels(function (data){
        if (data.length !== 0){
            data.forEach(function(pixel){
                changePixel(pixel[0], pixel[1], pixel[2]);
            })
        }
    });

    updateTime();
}

function countdown(t) {
    let offlineText = document.getElementById("offlineText");
    setTimeout(() => {
        let snd = " in " + t;
        if (t === 0)
            snd = ""
        offlineText.innerHTML = "You're not connected!<br>Retrying" + snd + "...";
        if (t > 0) {
            countdown(t - 1);
        }
    }, 1000);
}

function offlineHandler(){
    let offlineDiv = document.getElementById("offlineOverlay");

    console.log(offlineDiv, offlineText);
    offlineDiv.classList.remove("hidden");
    offlineText.classList.remove("hidden");
    let url = host + "/canvas/since?timestamp=" + (lastUpdate);
    let connected = false;
    fetch(url)
        .then(response => {
            if (response.status === 404){
                throw "offline";
            }
            loadImage();
            updateInterval(updateNewPixels, 1000);
            offlineDiv.classList.add("hidden");
            offlineText.classList.add("hidden");
            return;
        })
        .catch(error => {
            console.log("Still offline");
        });
    updateTime();
    countdown(5);
}