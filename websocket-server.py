#!/usr/bin/env python2
#
# Copyright 2015-2016 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
fileDir = os.path.dirname(os.path.realpath(__file__))
#sys.path.append(os.path.join(fileDir, "..", ".."))

import txaio
txaio.use_twisted()

from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
from twisted.internet import task, defer
from twisted.internet.ssl import DefaultOpenSSLContextFactory

from twisted.python import log

import argparse
import cv2
import imagehash
import json
from PIL import Image
import numpy as np
import os
import StringIO
import urllib
import base64

from sklearn.grid_search import GridSearchCV
from sklearn.manifold import TSNE
from sklearn.svm import SVC

import openface

modelDir = os.path.join(fileDir, 'openface', 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
# For TLS connections
tls_crt = os.path.join(fileDir, 'certificates', 'server.crt')
tls_key = os.path.join(fileDir, 'certificates', 'server.key')

parser = argparse.ArgumentParser()
parser.add_argument('--dlibFacePredictor', type=str, help="Path to dlib's face predictor.",
                    default=os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
parser.add_argument('--networkModel', type=str, help="Path to Torch network model.",
                    default=os.path.join(openfaceModelDir, 'nn4.small2.v1.t7'))
parser.add_argument('--imgDim', type=int,
                    help="Default image dimension.", default=96)
parser.add_argument('--cuda', action='store_true')
parser.add_argument('--unknown', type=bool, default=False,
                    help='Try to predict unknown people')
parser.add_argument('--port', type=int, default=9000,
                    help='WebSocket Port')
parser.add_argument('--threshold', type=float, default=0.75, help='Prediction precision percetage threshold')

args = parser.parse_args()

align = openface.AlignDlib(args.dlibFacePredictor)
net = openface.TorchNeuralNet(args.networkModel, imgDim=args.imgDim,
                              cuda=args.cuda)


class Face:

    def __init__(self, rep, identity):
        self.rep = rep
        print(rep) # TODO remove this
        self.identity = identity

    def __repr__(self):
        return "{{id: {}, rep[0:5]: {}}}".format(
            str(self.identity),
            self.rep[0:5]
        )


class OpenFaceServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super(OpenFaceServerProtocol, self).__init__()
        self.faces = {}
        self.identityNames = {}
        self.people = []
        self.svm = None

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")
        
    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


    def onMessage(self, payload, isBinary):
        raw = payload.decode('utf8')
        message = json.loads(raw)
        print("Received {} message of length {}.".format(
            message['type'], len(raw)))
        if message['type'] == "FRAME":

            name = None
            if 'name' in message:
                name = message['name']
            self.processFrame(message['image'], name, message['uuid'])
            
        else:
            print("Warning: Unknown message type: {}".format(message['type']))

    def getData(self):
        X = [] # Representations
        y = [] # Identities

        # for img in self.faces.values():
        #     X.append(img.rep)
        #     y.append(img.identity)

        facesDictionary = {}
        for img in self.faces.values():
            representation = img.rep
            identity = img.identity
            if identity not in facesDictionary:
                facesDictionary[identity] = []
            representationList = facesDictionary[identity]
            representationList.append(representation)

        for key, value in facesDictionary.items():
            representationCount = len(value)
            if representationCount >= 5:
                X.extend(value)
                y.extend([key] * representationCount)
        

        numIdentities = len(set(y + [-1])) - 1
        if numIdentities == 0:
            return None

        X = np.vstack(X)
        y = np.array(y)
        return (X, y)

    def trainSVM(self):
        print("+ Training SVM on {} labeled images.".format(len(self.faces)))
        d = self.getData()
        if d is None:
            self.svm = None
            return
        else:
            (X, y) = d
            numIdentities = len(set(y + [-1]))
            if numIdentities <= 1:
                return

            param_grid = [
                {'C': [1, 10, 100, 1000],
                 'kernel': ['linear']},
                {'C': [1, 10, 100, 1000],
                 'gamma': [0.001, 0.0001],
                 'kernel': ['rbf']}
            ]
            self.svm = GridSearchCV(SVC(C=1, probability=True), param_grid, cv=5).fit(X, y)

    def processFrame(self, image, name, uuid):
        imgdata = base64.b64decode(image)
        imgF = StringIO.StringIO()
        imgF.write(imgdata)
        imgF.seek(0)
        img = Image.open(imgF)

        buf = np.fliplr(np.asarray(img))
        rgbFrame = np.zeros((400, 400, 3), dtype=np.uint8)
        rgbFrame[:, :, 0] = buf[:, :, 2]
        rgbFrame[:, :, 1] = buf[:, :, 1]
        rgbFrame[:, :, 2] = buf[:, :, 0]

        unknownFacesCount = 0
        identities = []
        bbs = align.getAllFaceBoundingBoxes(rgbFrame)
        if len(bbs) == 0:
            # No faces found
            message = {
                'message' : "No faces found",
                'uuid' : uuid
            }
            self.sendMessage(json.dumps(message))
            return
        elif len(bbs) > 1 and name:
            # More than one face detected, cannot use picture to train
            message = {
                'message' : "More than one face detected, cannot use picture to train",
                'uuid' : uuid
            }
            self.sendMessage(json.dumps(message))
            return

        identity = -1
        if name != None:
            if name in self.identityNames:
                identity = self.identityNames[name]
            else:
                identity = len(self.identityNames)
                self.identityNames[name] = identity

        for bb in bbs:
            
            landmarks = align.findLandmarks(rgbFrame, bb)
            alignedFace = align.align(args.imgDim, rgbFrame, bb, landmarks=landmarks, landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

            phash = str(imagehash.phash(Image.fromarray(alignedFace)))
            if phash in self.faces:
                # Face has already been registered
                identity = self.faces[phash].identity
            else:
                #
                rep = net.forward(alignedFace)

                if name and len(bbs) == 1:
                    self.faces[phash] = Face(rep, identity)
                    message = {
                        'message' : "Face added",
                        'uuid' : uuid
                    }
                    self.sendMessage(json.dumps(message))
                    return
                else:
                    if len(self.people) == 0:
                        identity = -1
                    elif self.svm:
                        probabilities = self.svm.predict_proba(rep)[0]
                        highest = 0.0
                        index = 0
                        for i in range(len(probabilities)):
                            if probabilities[i] > highest:
                                highest = probabilities[i]
                                index = i
                            print(probabilities[i])
                        print("Highest Probability: {}".format(highest))
                        if highest > args.threshold:
                            identity = index
                        else:
                            unknownFacesCount = unknownFacesCount + 1
                            identity = -1
                        print("Predicted identity value: {}".format(identity))
                    else:
                        print("Something went wrong predicting")
                        identity = -1

                    if identity not in identities:
                        identities.append(identity)

        if not name:

            message = {
                'unknownFacesCount' : unknownFacesCount
            }

            if len(identities) > 0:

                people = set()
                
                for identity in identities:

                    if identity == -1:
                        name = "Unknown"
                    else:
                        name = self.people[identity]

                    people.add(name)

                message['people'] = list(people)

            message['uuid'] = uuid
            self.sendMessage(json.dumps(message))
            print("Predicted People: {}".format(str(message['people'])))

def main(reactor):
    log.startLogging(sys.stdout)
    factory = WebSocketServerFactory()
    factory.protocol = OpenFaceServerProtocol
    ctx_factory = DefaultOpenSSLContextFactory(tls_key, tls_crt)
    reactor.listenSSL(args.port, factory, ctx_factory)
    return defer.Deferred()

if __name__ == '__main__':
    task.react(main)