#!/bin/bash

killall npm
killall node
killall python

python websocket-server.py --threshold 0.75 >> logs/python-server.log &

sleep 5

npm run start >> logs/node-server.log &

