exports.addFace = function(request, response){

    var responseServed = false;

    var image = request.file;

    var name = request.body.name;

    var uuid = generateUUID();

    const imagePath = image.path;

    spawnSync('python',["./resize.py", imagePath]);

    var data = fs.readFileSync(imagePath + ".jpg");

    var b64Image = data.toString("base64");

    var responseBody;

    if (socket != null) {

        var systemMessage = {
            'type': 'FRAME',
            'image': b64Image,
            'name' : name,
            'uuid' : uuid
        };
        socket.send(JSON.stringify(systemMessage));

        if (name){
            if (!responseServed){

                responseBody = {
                    success : true,
                    message : "Picture added"
                };

                responseServed = true;
                response.json(responseBody);
            }
			
        } else {

            function onMessageReceived(data) {
                
                console.log("Message Received from Python: " + JSON.stringify(data));

                if (!responseServed){
                    if (data.hasOwnProperty("people")){

                        responseBody = {
                            success : true,
                            predictions : data.people,
                            unknownFacesCount : data.unknownFacesCount
                        };
                
                        response.json(responseBody);
                        responseServed = true;
                    } else {
                        responseBody = {
                            success : true,
                            message : data.message
                        };
                
                        response.json(responseBody);
                        responseServed = true;
                    }
                }
                registeredCallbacks.delete(uuid);
            }
            registeredCallbacks.set(uuid, onMessageReceived);
        }
    } else {
        
        responseBody = {
            success : false,
            message : "Connection with OpenFace Server Failed"
        };
        if (!responseServed){
            responseServed = true;
            response.json(responseBody);
        }
        
    }


    setTimeout(function () {

        responseBody = {
            success : false,
            message : "Prediction Timed Out"
        };
        if (!responseServed){
            responseServed = true;
            response.json(responseBody);
        }
        
    }, 5000);

}