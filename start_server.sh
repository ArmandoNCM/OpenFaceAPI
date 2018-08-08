#!/bin/bash

killall python
killall npm
killall node

python openface/demos/web/websocket-server.py &

sleep 5

npm run start &

