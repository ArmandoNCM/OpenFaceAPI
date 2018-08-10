exports.addFace = function(request, response){

    var responseServed = false;

    var isTraining = request.body.training;

    var image = request.file;

    var name = request.body.name;

    var identity;

    if (name != null && identities.has(name)){
        identity = parseInt(identities.get(name))
    } else {
        identity = -1
    }

    const imagePath = image.path;

    const pythonProcess = spawnSync('python',["./resize.py", imagePath]);

    var data = fs.readFileSync(imagePath + ".jpg");

    var b64Image = "data:image/jpeg;base64," + data.toString("base64");

    var socketInputCount = 0;

    var responseBody;

    if (socket != null) {

        var systemMessage = {
            'type': 'FRAME',
            'dataURL': b64Image,
            'identity': identity
        };
        socket.send(JSON.stringify(systemMessage));

        if (isTraining){
            if (!responseServed){

                responseBody = {
                    success : true,
                    message : "Picture added"
                };

                responseServed = true;
                response.json(responseBody);
            }
			
        } else {

            socket.on('message', function incoming(data) {
                
                socketInputCount++;
                console.log("Socket Input Count: " + socketInputCount);
                console.log("Message Received from Python: " + data);

                var object = JSON.parse(data);
                if (!responseServed && object.hasOwnProperty("people")){

                    responseBody = {
                        success : true,
                        predictions : object.people,
                        unknownFacesCount : object.unknownFacesCount
                    };
            
                    response.json(responseBody);
                    responseServed = true;
                } 
                /*else {
                    responseBody = {
                        success : true,
                        message : object.message
                    };
            
                    response.json(responseBody);
                    responseServed = true;
                }*/
                
            });
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

exports.setTrainingState = function(request, response){

    var newIsTrainingValue = request.body.isTraining;

    var name = request.body.name;

    var responseBody;

    if (socket != null) {

        var systemMessage;

        if (newIsTrainingValue && !identities.has(name)){

            identities.set(name, identities.size)

            systemMessage = {
                'type' : 'ADD_PERSON',
                'val' : name
            }
            socket.send(JSON.stringify(systemMessage));
        }

        systemMessage = {
            'type' : 'TRAINING',
            'val' : newIsTrainingValue
        };
        socket.send(JSON.stringify(systemMessage));
        
        responseBody = {
            success : true,
            message : "Training Active State: " + String(newIsTrainingValue)
        };
    } else {
        
        responseBody = {
            success : false,
            message : "Connection with OpenFace Server Failed"
        };
    }

    response.json(responseBody);
}