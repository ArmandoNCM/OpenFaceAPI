module.exports = function(app){

    let faceRecognitionController = require("../controllers/faceRecognitionController");

    app.route("/openface")
        .post(faceRecognitionController.addFace);
}
