#!/usr/bin/env bash

docker run -it --rm --network=host \
-v /path_to_your/config.ini:/app/config.ini \
stremio-download:latest