#!/bin/bash

# Print helper menu
print_help() {
  echo "Usage: $0 SERIES_URL [SEASON] [EP_FROM] [EP_TO] [IS_RD]"
  echo
  echo "SERIES_URL: URL of the series to be processed."
  echo "SEASON: Season number (default is 1)."
  echo "EP_FROM: Starting episode number (default is blank)."
  echo "EP_TO: Ending episode number (default is blank)."
  echo "IS_RD: Boolean indicating whether it's RD or not (default is true)."
  echo
  echo "Example: $0 http://example.com/series 1 1 10 true"
  exit 1
}

# Check for the mandatory argument
if [ -z "$1" ]; then
  print_help
fi

# Customize these
USERNAME="STREMIO_USERNAME"
PASSWORD="STREMIO_PASSWORD"
SERIES_URL=$1
SEASON=${2:-"1"}
EP_FROM=${3:-""}
EP_TO=${4:-""}
IS_RD=${5:-"true"}
METUBE_URL="http://10.0.0.46:9582/add"

#No changes needed - usually
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
HEADERS=(
  "-H 'Connection: close'"
  "-H 'User-Agent: $USER_AGENT'"
  "-H 'Accept: application/json, text/plain, */*'"
  "-H 'Accept-Language: en-US,en;q=0.5'"
  "-H 'Accept-Encoding: gzip, deflate'"
  "-H 'Content-Type: application/json'"
  "-H 'Origin: $METUBE_URL'"
  "-H 'Connection: keep-alive'"
  "-H 'Referer: $METUBE_URL/'"
  "-H 'Cookie: metube_theme=auto'"
  "-H 'Priority: u=0'"
  "-H 'Pragma: no-cache'"
  "-H 'Cache-Control: no-cache'"
)

# Function to send a URL to MeTube
send_url_to_metube() {
  local url=$1
  echo "MeTube: "
  curl -s "$METUBE_URL" -X POST "${HEADERS[@]}" --data-raw "{\"url\":\"$url\",\"quality\":\"best\",\"format\":\"any\",\"auto_start\":true}"
}

# Function to process URLs and send them to MeTube
process_input_urls() {
  while read -r line; do
    if [[ $line == https://* ]]; then
      line=$(echo "$line" | sed 's/\r//')
      send_url_to_metube "$line"
    fi
  done
}

extract_and_process_bulk_print() {
  local log="$1"
  echo "$log" | awk '/-----Bulk Print for easy copy---------/{flag=1; next} /--------------------------------------/{flag=0} flag' | process_input_urls
}

# Run the docker command and process URLs for MeTube
log=$(docker run -it --rm \
  --env USERNAME=$USERNAME \
  --env PASSWORD=$PASSWORD \
  --env SERIES_URL=$SERIES_URL \
  --env FROM=$EP_FROM \
  --env TO=$EP_TO \
  --env SEASON=$SEASON \
  --env IS_RD=$IS_RD \
  stremio-download:0.0.2 | tee /dev/tty)
extract_and_process_bulk_print "$log"

echo "Completed."