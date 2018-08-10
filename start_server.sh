#!/bin/bash

killall python
killall npm
killall node

python websocket-server.py --threshold 0.7 &

sleep 15

npm run start &

