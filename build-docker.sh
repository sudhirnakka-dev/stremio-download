#!/usr/bin/env bash

docker build -t sudhirnakka07/stremio-download:0.0.2 .
docker tag sudhirnakka07/stremio-download:0.0.2 sudhirnakka07/stremio-download:latest
