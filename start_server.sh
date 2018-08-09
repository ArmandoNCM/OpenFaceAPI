#!/bin/bash

killall python
killall npm
killall node

python openface/demos/web/websocket-server.py &

sleep 15

npm run start &

