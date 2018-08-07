module.exports = function(app){

    let faceRecognitionController = require("../controllers/faceRecognitionController");

    app.route("/openface")
        .post(upload.single("image"), faceRecognitionController.addFace)
        .put(faceRecognitionController.setTrainingState);
}