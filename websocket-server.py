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
import numpy
import os
import StringIO
import urllib
import base64

from sklearn.grid_search import GridSearchCV
from sklearn.manifold import TSNE
from sklearn.svm import SVC

import openface

persistenceDir = os.path.join(fileDir, 'persistence')
modelDir = os.path.join(fileDir, 'openface', 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
# For TLS connections
tls_crt = os.path.join(fileDir, 'certificates', 'server.crt')
tls_key = os.path.join(fileDir, 'certificates', 'server.key')

parser = argparse.ArgumentParser()
parser.add_argument('--noiseSeed', type=str, help="Path to state persistence file.",
                    default=os.path.join(fileDir, "noise.json"))
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


class OpenFaceServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super(OpenFaceServerProtocol, self).__init__()
        print("Creating OpenFaceServerProtocol instance")
        self.faces = {}
        self.identityNames = {}
        self.svm = None

    def onConnect(self, request):
        self.namespace = request.headers['namespace']
        self.statePersistencePath = os.path.join(persistenceDir, "{}.json".format(self.namespace))
        print("Client connecting: {0}, Namespace:{1}".format(request.peer, self.namespace))

    def onOpen(self):
        print("WebSocket connection open.")

        try:
            print("Reading Noise Seed Data")
            statePersistenceFile = open(args.noiseSeed, 'r')
            state = json.load(statePersistenceFile)
            faces = state['faces']
            for value in faces.values():
                complexRepresentation = numpy.asanyarray(value['representation']) 
                value['representation'] = complexRepresentation
            self.noiseFaces = faces
            self.noiseIdentityNames = state['identityNames']
            statePersistenceFile.close()
            self.trainSVM()
            
            if os.path.exists(self.statePersistencePath):
                print("Reading Saved State Data")
                statePersistenceFile = open(self.statePersistencePath, 'r')
                state = json.load(statePersistenceFile)
                faces = state['faces']
                for value in faces.values():
                    complexRepresentation = numpy.asanyarray(value['representation']) 
                    value['representation'] = complexRepresentation
                self.faces = faces
                self.identityNames = state['identityNames']
                statePersistenceFile.close()
                self.trainSVM()
            
        except RuntimeError as e:
            print("Failed")
            print(e)
        
    def onClose(self, wasClean, code, reason):
        print("WebSocket connection with namespace {0} closed: {1}".format(self.namespace, reason))

        for value in self.faces.values():
            simplifiedRepresentation = value['representation'].tolist()
            value['representation'] = simplifiedRepresentation

        stateData = {
            'faces' : self.faces,
            'identityNames' : self.identityNames
        }
        stateDataJson = json.dumps(stateData)
        statePersistenceFile = open(self.statePersistencePath, 'w')
        statePersistenceFile.write(stateDataJson)
        statePersistenceFile.close()



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

        elif message['type'] == "PING":
            message = {
                'message' : message['message'],
                'success' : True
            }
            self.sendMessage(json.dumps(message))
            
        else:
            print("Warning: Unknown message type: {}".format(message['type']))

    def getData(self):
        X = [] # Representations
        y = [] # Identities

        for key, value in self.noiseFaces.items():
            self.faces[key] = value
        
        for key, value in self.noiseIdentityNames.items():
            self.identityNames[key] = value

        facesDictionary = {}
        for img in self.faces.values():
            representation = img['representation']
            identity = img['identity']
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

        X = numpy.vstack(X)
        y = numpy.array(y)
        return (X, y)

    def trainSVM(self):
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

        buf = numpy.fliplr(numpy.asarray(img))
        rgbFrame = numpy.zeros((400, 400, 3), dtype=numpy.uint8)
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
                'uuid' : uuid,
                'success' : False
            }
            self.sendMessage(json.dumps(message))
            return
        elif len(bbs) > 1 and name != None:
            # More than one face detected, cannot use picture to train
            print("More than one face detected, cannot use picture to train")
            message = {
                'message' : "More than one face detected, cannot use picture to train",
                'uuid' : uuid,
                'success' : False
            }
            self.sendMessage(json.dumps(message))
            return

        identity = -1
        if name != None:
            name = name.encode('ascii', 'ignore')
            if name in self.identityNames:
                identity = self.identityNames[name]
            else:
                identity = len(self.identityNames)
                

        for bb in bbs:
            
            landmarks = align.findLandmarks(rgbFrame, bb)
            alignedFace = align.align(args.imgDim, rgbFrame, bb, landmarks=landmarks, landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)

            phash = str(imagehash.phash(Image.fromarray(alignedFace)))
            if phash in self.faces:
                # Face has already been registered
                if name:
                    message = {
                        'message' : "Face has already been added",
                        'success' : False,
                        'uuid' : uuid
                    }
                    self.sendMessage(json.dumps(message))
                    return
                else:
                    identity = self.faces[phash]['identity']
                    identities.append(identity)

            else:
                #
                representation = net.forward(alignedFace)

                if name and len(bbs) == 1:
                    self.identityNames[name] = identity
                    self.faces[phash] = {
                        'representation' : representation,
                        'identity' : identity
                    }
                    self.trainSVM()
                    message = {
                        'message' : "Face added, Child ID: {}".format(name),
                        'uuid' : uuid,
                        'success' : True
                    }
                    self.sendMessage(json.dumps(message))
                    return
                else:
                    if self.svm:
                        probabilities = self.svm.predict_proba(representation)[0]
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
                        for key, value in self.identityNames.items():
                            if value == identity:
                                name = key
                                break

                    people.add(name)

                message['people'] = list(people)

            message['uuid'] = uuid
            message['success'] = True
            self.sendMessage(json.dumps(message))
            peopleOutput = []
            if 'people' in message:
                peopleOutput = message['people']
            print("Predicted People: {}".format(str(peopleOutput)))

def main(reactor):
    log.startLogging(sys.stdout)
    factory = WebSocketServerFactory()
    factory.protocol = OpenFaceServerProtocol
    ctx_factory = DefaultOpenSSLContextFactory(tls_key, tls_crt)
    reactor.listenSSL(args.port, factory, ctx_factory)
    return defer.Deferred()

if __name__ == '__main__':
    task.react(main)
