#!/bin/bash

cd ./steve_carell

curl -H 'Content-Type: application/json' -X PUT -d '{"isTraining":true,"name":"SteveCarell"}' localhost:3000/openface

curl -X POST -F name="SteveCarell" -F training=true -F image=@1.jpg localhost:3000/openface
curl -X POST -F name="SteveCarell" -F training=true -F image=@2.jpg localhost:3000/openface
curl -X POST -F name="SteveCarell" -F training=true -F image=@3.jpg localhost:3000/openface
curl -X POST -F name="SteveCarell" -F training=true -F image=@4.jpg localhost:3000/openface
curl -X POST -F name="SteveCarell" -F training=true -F image=@5.jpg localhost:3000/openface

sleep 1

curl -H 'Content-Type: application/json' -X PUT -d '{"isTraining":false}' localhost:3000/openface

cd ..

cd ./john_cena

curl -H 'Content-Type: application/json' -X PUT -d '{"isTraining":true,"name":"JohnCena"}' localhost:3000/openface

curl -X POST -F name="JohnCena" -F training=true -F image=@1.jpg localhost:3000/openface
curl -X POST -F name="JohnCena" -F training=true -F image=@2.jpg localhost:3000/openface
curl -X POST -F name="JohnCena" -F training=true -F image=@3.jpg localhost:3000/openface
curl -X POST -F name="JohnCena" -F training=true -F image=@4.jpg localhost:3000/openface
curl -X POST -F name="JohnCena" -F training=true -F image=@5.jpg localhost:3000/openface

sleep 1

curl -H 'Content-Type: application/json' -X PUT -d '{"isTraining":false}' localhost:3000/openface

