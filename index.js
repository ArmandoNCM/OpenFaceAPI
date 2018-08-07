process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const WebSocket = require("ws");

socket = new WebSocket("wss:10.0.0.1:9000");

fs = require("fs");

var multer  = require('multer')

upload = multer({ dest: 'uploads/' })

const express = require("express");

const bodyParser = require('body-parser');

const app = express();

const port = 3000;

const faceRecognitionRoutes = require("./api/routes/faceRecognitionRoutes");

app.use(bodyParser.json());

faceRecognitionRoutes(app);

app.listen(port);

console.log("Listening on port: " + port);