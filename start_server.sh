#!/bin/bash

python openface/demos/web/websocket-server.py &

sleep 5

npm run start &

while true; do
    read -rsn1 input
    if [ "$input" = "q" ]; then 
        echo Finishing and Cleaning Up
	killall python
	killall npm
	killall node
	exit          
    fi
done



