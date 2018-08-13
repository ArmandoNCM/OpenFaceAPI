process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
STATUS_SERVICE_UNAVAILABLE = 503;
STATUS_GATEWAY_TIMEOUT = 504;
STATUS_BAD_REQUEST = 400;

WebSocket = require("ws");

const uuidv4 = require('uuid/v4');

generateUUID = uuidv4;

registeredConnections = new Map();

resetTimeout = function(connection){
    if (connection.timeOut){
        clearTimeout(connection.timeOut);
    }

    connection.timeOut = setTimeout(function(){
        connection.socket.terminate();
        connection.registeredCallbacks.clear();
        if (registeredConnections.has(connection.id)){
            registeredConnections.delete(connection.id);
        }
    }, 120000)
}

connectionWithPythonFailed = function(response){

    responseBody = {
        success : false,
        message : "Connection with OpenFace Server Failed"
    }
    response.status(STATUS_SERVICE_UNAVAILABLE).json(responseBody);
}

fs = require("fs");

spawnSync = require("child_process").spawnSync;

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
