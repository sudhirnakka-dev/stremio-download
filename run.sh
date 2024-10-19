#!/usr/bin/env bash

export USERNAME="USERNAME"
export PASSWORD="PASSWORD"
export SERIES_URL="https://web.stremio.com/#/detail/series/tt1218?season=1"
export SEASON="1"
export FROM="10" #Optional - Can comment
export TO="12" #Optional - Can comment
export IS_RD="true" #Optional - Can comment
export NAME_CONTAINS="Judas" #Optional - Can comment

python main_env.py