exports.addFace = function(request, response){

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