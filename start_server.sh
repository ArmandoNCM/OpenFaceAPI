#!/bin/bash

killall python
killall npm
killall node

python websocket-server.py --threshold 0.7 >> logs/python-server.log &

sleep 15

npm run start >> logs/node-server.log &

