exports.addFace = function(request, response){

    var image = request.file;

    var identity = parseInt(request.body.identity);

    const imagePath = image.path;

    const pythonProcess = spawn('python',["../../resize.py", imagePath]);

    var data = fs.readFileSync(imagePath);

    var b64Image = "data:image/jpeg;base64," + data.toString("base64");

    var responseBody;

    if (socket != null) {

        var systemMessage = {
            'type': 'FRAME',
            'dataURL': b64Image,
            'identity': identity
        };
        socket.send(JSON.stringify(systemMessage));

        responseBody = {
            success : true,
            message : "Picture added"
        };
    } else {
        
        responseBody = {
            success : false,
            message : "Connection with OpenFace Server Failed"
        };
    }

    response.json(responseBody);

}

exports.setTrainingState = function(request, response){

    var isTrainingValue = request.body.isTraining;

    var id = request.body.id;

    var responseBody;

    if (socket != null) {

        var systemMessage;

        systemMessage = {
            'type' : 'TRAINING',
            'val' : isTrainingValue
        };
        socket.send(JSON.stringify(systemMessage));

        if (isTrainingValue){
            systemMessage = {
                'type' : 'ADD_PERSON',
                'val' : id
            }
            socket.send(JSON.stringify(systemMessage));
        }
        responseBody = {
            success : true,
            message : "Training Active State: " + String(isTrainingValue)
        };
    } else {
        
        responseBody = {
            success : false,
            message : "Connection with OpenFace Server Failed"
        };
    }

    response.json(responseBody);
}