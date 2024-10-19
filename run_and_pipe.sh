#!/bin/bash

# Define the constant values
METUBE_URL="http://10.0.0.46:9582/add"
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
  --env USERNAME="USERNAME" \
  --env PASSWORD="PASSWORD" \
  --env SERIES_URL="https://web.stremio.com/#/detail/series/tt1112349" \
  --env FROM="10" \
  --env TO="12" \
  --env SEASON="1" \
  --env IS_RD="true" \
  stremio-download:0.0.2 | tee /dev/tty)
extract_and_process_bulk_print "$log"

echo "Completed."