#!/usr/bin/env bash

docker build -t stremio-download:0.0.2 .
docker tag stremio-download:0.0.2 stremio-download:latest
