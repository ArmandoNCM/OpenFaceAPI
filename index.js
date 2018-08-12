process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const WebSocket = require("ws");

socket = new WebSocket("wss:localhost:9000");

const uuidv4 = require('uuid/v4');

generateUUID = uuidv4;

registeredCallbacks = new Map();

function onMessageReceived(message) {

    var data = JSON.parse(message);
    if (data.hasOwnProperty("uuid")){

        var uuid = data.uuid;
        if (registeredCallbacks.has(uuid)){

            var callbackFunction = registeredCallbacks.get(uuid);
            callbackFunction(data);
        }
    }
}

socket.on('message', onMessageReceived);

fs = require("fs");

spawnSync = require("child_process").spawnSync;

identities = new Map();

const formData = require("express-form-data");

const express = require("express");

const app = express();

const port = 27500;

const faceRecognitionRoutes = require("./api/routes/faceRecognitionRoutes");

const options = {
    uploadDir: 'uploads',
    autoClean: true
};
app.use(formData.parse(options));
app.use(formData.union());

faceRecognitionRoutes(app);

app.listen(port);

console.log("Listening on port: " + port);
