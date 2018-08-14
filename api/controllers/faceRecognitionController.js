exports.addFace = function(request, response){

    var responseServed = false;

    var image = request.files.image;

    var name = request.body.name;

    var namespace = request.body.namespace;

    if (!namespace){
        responseServed = true;
        var badRequestMessage = {
            success : false,
            message : "Missing namespace field"
        }
        response.status(STATUS_BAD_REQUEST).json(badRequestMessage);
	    return;
    }
    if (!image){
        responseServed = true;
        var badRequestMessage = {
            success : false,
            message : "Missing image field"
        }
        response.status(STATUS_BAD_REQUEST).json(badRequestMessage);
	    return;
    }

    var connection;
    var freshConnection = false;
    if (registeredConnections.has(namespace)){
        connection = registeredConnections.get(namespace);
        if (connection.isAlive){
            resetTimeout(connection);
        } else {
            connection = null;
        }
    } 
    if (connection == null) {
        freshConnection = true;
        try{
            console.log("Opening new connection to Python Web Server with ID: " + namespace);
            connection = {
                isAlive : true,
                namespace : namespace,
                socket : new WebSocket("wss:localhost:9000", [], {headers: {namespace : namespace}}),
                registeredCallbacks : new Map()
            }
            aux = connection.socket;
            registeredConnections.set(namespace, connection);

            function onIncomingMessage(message) {
                var data = JSON.parse(message);
                if (data.hasOwnProperty("uuid")){
            
                    var uuid = data.uuid;
                    if (connection.registeredCallbacks && connection.registeredCallbacks.has(uuid)){
            
                        var callbackFunction = connection.registeredCallbacks.get(uuid);
                        callbackFunction(data);
                    }
                }
            }
            connection.socket.on('message', onIncomingMessage);

            resetTimeout(connection);

        } catch (error) {
            console.log(error);
            connectionWithPythonFailed(response);
        }
    }

    var uuid = generateUUID();

    const imagePath = image.path;

    spawnSync('python',["./resize.py", imagePath]);

    var data = fs.readFileSync(imagePath + ".jpg");

    var b64Image = data.toString("base64");

    var responseBody;

    function sendMessage(){

        var systemMessage = {
            'type': 'FRAME',
            'image': b64Image,
            'name' : name,
            'uuid' : uuid
        };
    
        try {
            connection.socket.send(JSON.stringify(systemMessage));
        } catch (error) {
            console.log(error);
            if (!responseServed){
                responseServed = true;
                connectionWithPythonFailed(response);
            }
        }
    }

    function onMessageReceived(data) {
        
        console.log("Message Received from Python: " + JSON.stringify(data));

        if (!responseServed){
            if (data.hasOwnProperty("people")){

                responseBody = {
                    success : data.success,
                    predictions : data.people,
                    unknownFacesCount : data.unknownFacesCount
                };
        
                response.json(responseBody);
                responseServed = true;
            } else {
                responseBody = {
                    success : data.success,
                    message : data.message
                };
        
                response.json(responseBody);
                responseServed = true;
            }
        }
        connection.registeredCallbacks.delete(uuid);
    }
    connection.registeredCallbacks.set(uuid, onMessageReceived);

    if (freshConnection) {

        connection.socket.on('open', sendMessage);
    } else {

        sendMessage();
    }

    setTimeout(function () {

        responseBody = {
            success : false,
            message : "Prediction Timed Out"
        };
        if (!responseServed){
            responseServed = true;
            response.status(STATUS_GATEWAY_TIMEOUT).json(responseBody);
        }
        
    }, 30000);

}
