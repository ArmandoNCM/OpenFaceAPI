exports.addFace = function(request, response){

    var image = request.file;

    var id = request.body.id;

    var data = fs.readFileSync(image.path);

    var b64Image = "data:image/jpeg;base64," + data.toString("base64");

    var responseBody;

    if (socket != null) {

        var systemMessage = {
            'type': 'FRAME',
            'dataURL': b64Image,
            'identity': id
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

    var value = request.body.isTraining;

    var responseBody;

    if (socket != null) {

        var systemMessage = {
            'type' : 'TRAINING',
            'val' : value
        };
        socket.send(JSON.stringify(systemMessage));

        responseBody = {
            success : true,
            message : "Training Active State: " + String(value)
        };
    } else {
        
        responseBody = {
            success : false,
            message : "Connection with OpenFace Server Failed"
        };
    }

    response.json(responseBody);
}