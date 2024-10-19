#!/usr/bin/env bash

docker build -t stremio-download:0.0.1 .
docker tag stremio-download:0.0.1 stremio-download:latest
