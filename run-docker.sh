#!/usr/bin/env bash

# Following are optional env vars. Can be added/removed based on the need
#--env FROM="10" \
#--env TO="20" \
#--env IS_RD="true" \
#--env NAME_CONTAINS="Judas" \

docker run -it --rm \
--env USERNAME="USERNAME" \
--env PASSWORD="PASSWORD" \
--env SERIES_URL="https://web.stremio.com/#/detail/series/tt0012349" \
--env SEASON="1" \
--env FROM="10" \
--env TO="20" \
--env IS_RD="true" \
--env NAME_CONTAINS="Judas" \
sudhirnakka07/stremio-download:0.0.2