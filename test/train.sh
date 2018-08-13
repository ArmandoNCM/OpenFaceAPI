#!/bin/bash

cd ./steve_carell

curl -X POST -F namespace="TestNamespace" -F name="SteveCarell" -F image=@1.jpg localhost:27500/openface
curl -X POST -F namespace="TestNamespace" -F name="SteveCarell" -F image=@2.jpg localhost:27500/openface
curl -X POST -F namespace="TestNamespace" -F name="SteveCarell" -F image=@3.jpg localhost:27500/openface
curl -X POST -F namespace="TestNamespace" -F name="SteveCarell" -F image=@4.jpg localhost:27500/openface
curl -X POST -F namespace="TestNamespace" -F name="SteveCarell" -F image=@5.jpg localhost:27500/openface
