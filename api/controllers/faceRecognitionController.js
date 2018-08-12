const STATUS_SERVICE_UNAVAILABLE = 503;
const STATUS_GATEWAY_TIMEOUT = 504;

exports.addFace = function(request, response){

    var responseServed = false;

    var image = request.files.image;

    var name = request.body.name;

    var uuid = generateUUID();

    const imagePath = image.path;

    spawnSync('python',["./resize.py", imagePath]);

    var data = fs.readFileSync(imagePath + ".jpg");

    var b64Image = data.toString("base64");

    var responseBody;


    var systemMessage = {
        'type': 'FRAME',
        'image': b64Image,
        'name' : name,
        'uuid' : uuid
    };
    try {
        socket.send(JSON.stringify(systemMessage));
    } catch (error) {
        responseBody = {
            success : false,
            message : "Connection with OpenFace Server Failed"
        };
        if (!responseServed){
            responseServed = true;
            response.status(STATUS_SERVICE_UNAVAILABLE).json(responseBody);
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
        registeredCallbacks.delete(uuid);
    }
    registeredCallbacks.set(uuid, onMessageReceived);

    setTimeout(function () {

        responseBody = {
            success : false,
            message : "Prediction Timed Out"
        };
        if (!responseServed){
            responseServed = true;
            response.status(STATUS_GATEWAY_TIMEOUT).json(responseBody);
        }
        
    }, 5000);

}