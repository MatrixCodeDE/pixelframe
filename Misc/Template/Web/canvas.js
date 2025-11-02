document.addEventListener("DOMContentLoaded", init);
let host;
let canvas;
let canvasContainer;
let ctx;
let lastUpdate;
let interval;
let positionPopup;
let fullscreenButton;
let isFullscreen;
let inactivityTimer;
const inactivityLimit = 5000;

function init(event) {
    if (window.location.port !== ""){
        host = "http://" + window.location.hostname + ":" + window.location.port;
    } else {
        host = "http://" + window.location.hostname;
    }
    canvas = document.getElementById("canvas");
    canvasContainer = document.getElementById("canvasContainer");
    positionPopup = document.getElementById("positionPopup");
    fullscreenButton = document.getElementById("fullScreenButton");
    ctx = canvas.getContext("2d");
    lastUpdate = new Date().getTime();
    resizeCanvas();
    loadImage();
    interval = setInterval(updateNewPixels, 1000);

    canvas.addEventListener("mousemove", cursorPosition);
    canvas.addEventListener("mouseleave", cursorExitCanvas);
    canvas.addEventListener("click", positionPopupToggle);
    fullscreenButton.addEventListener("click", toggleFullscreen);
    isFullscreen = false;

    document.addEventListener("mousemove", resetInactivity);
    document.addEventListener("keydown", resetInactivity);
    document.addEventListener("click", resetInactivity);
    document.addEventListener("scroll", resetInactivity);
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
        if (xhrImg.status >= 200 && xhrImg.status < 300) {
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
    let url = host + "/canvas/since?timestamp=" + (lastUpdate - 0);
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

function changePixels(pixels){
    let imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    let dat = imgData.data;

    pixels.forEach(function(pixel) {
        let x = pixel[0];
        let y = pixel[1];
        let color = pixel[2];

        let [r, g, b] = hexToRgb(color);

        let index = (y * canvas.width + x) * 4;

        dat[index] = r;
        dat[index + 1] = g;
        dat[index + 2] = b;
        dat[index + 3] = 255;
    }
    );

    ctx.putImageData(imgData, 0, 0);
}

function updateNewPixels() {

    getNewPixels(function (data){
        if (data.length !== 0){
            changePixels(data)
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

function cursorPosition(event) {
    if (positionPopup.classList.contains("hidden"))
        return
    let rect = canvas.getBoundingClientRect();

    let scaleX = canvas.width / rect.width;
    let scaleY = canvas.height / rect.height;

    let x = (event.clientX - rect.left) * scaleX;
    let y = (event.clientY - rect.top) * scaleY;

    x = Math.round(x);
    y = Math.round(y);

    positionPopup.textContent = `X: ${x}, Y: ${y}`;
    positionPopup.style.left = `${event.clientX + 10}px`;
    positionPopup.style.top = `${event.clientY + 10}px`;

    positionPopup.style.display = "inline-block";
}

function cursorExitCanvas() {
    positionPopup.style.display = "none";
}

function positionPopupToggle(event) {
    positionPopup.classList.toggle("hidden");
    cursorPosition(event)
}

function addFullscreenChanger() {
    document.addEventListener("fullscreenchange", function() {
        if (!document.fullscreenElement){
            toggleFullscreen(null);
        }
    });

    document.addEventListener("webkitfullscreenchange", function() {
        if (!document.webkitFullscreenElement){
            toggleFullscreen(null);
        }
    });

    document.addEventListener("mozfullscreenchange", function() {
        if (!document.mozFullScreenElement){
            toggleFullscreen(null);
        }
    });

    document.addEventListener("msfullscreenchange", function() {
        if (!document.msFullscreenElement){
            toggleFullscreen(null);
        }
    });
}

function toggleFullscreen(event){
    document.getElementById("enableFullscreenSVG").classList.toggle("hidden");
    document.getElementById("disableFullscreenSVG").classList.toggle("hidden");
    if (isFullscreen && event) {
        exitFullscreen(event);
    } else {
        enterFullscreen(event);
    }
    isFullscreen = !isFullscreen;
}

function enterFullscreen(event) {
    if (canvasContainer.requestFullscreen) {
        canvasContainer.requestFullscreen();
    } else if (canvasContainer.mozRequestFullScreen) {
        canvasContainer.mozRequestFullScreen();
    } else if (canvasContainer.webkitRequestFullscreen) {
        canvasContainer.webkitRequestFullscreen();
    } else if (canvasContainer.msRequestFullscreen) {
        canvasContainer.msRequestFullscreen();
    }
}

function exitFullscreen(event) {
    if (document.exitFullscreen) {
        document.exitFullscreen();
    } else if (document.mozCancelFullScreen) {
        document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
    }
}

function resetInactivity(event) {
    clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(onInactivity, inactivityLimit, true);
    onInactivity(false);
}

function onInactivity(inactive){
    let elems = document.querySelectorAll(".activityRequired");
    elems.forEach(elem => {
        if (elem.classList.contains("inactive") !== inactive){
            elem.classList.toggle("active");
            elem.classList.toggle("inactive");
        }
    });


}