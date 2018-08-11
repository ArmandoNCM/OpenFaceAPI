#!/bin/bash

cd ./steve_carell

curl -X POST -F name="SteveCarell" -F image=@1.jpg localhost:27500/openface
curl -X POST -F name="SteveCarell" -F image=@2.jpg localhost:27500/openface
curl -X POST -F name="SteveCarell" -F image=@3.jpg localhost:27500/openface
curl -X POST -F name="SteveCarell" -F image=@4.jpg localhost:27500/openface
curl -X POST -F name="SteveCarell" -F image=@5.jpg localhost:27500/openface

cd ..

cd ./john_cena

curl -X POST -F name="JohnCena" -F image=@1.jpg localhost:27500/openface
curl -X POST -F name="JohnCena" -F image=@2.jpg localhost:27500/openface
curl -X POST -F name="JohnCena" -F image=@3.jpg localhost:27500/openface
curl -X POST -F name="JohnCena" -F image=@4.jpg localhost:27500/openface
curl -X POST -F name="JohnCena" -F image=@5.jpg localhost:27500/openface