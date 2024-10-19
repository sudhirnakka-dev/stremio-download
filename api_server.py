from flask import Flask, request, jsonify
from flask_cors import CORS

import main_env

app = Flask(__name__)
CORS(app)


@app.route('/api/series/add', methods=['POST'])
def add_series():
    print("Test")
    data = request.get_json()

    # Extract values from the JSON payload
    url = data.get('url')
    username = data.get('username')
    password = data.get('password')
    rd_only = data.get('rdOnly')
    season = data.get('season')
    episodes_from = data.get('episodesFrom')
    episodes_to = data.get('episodesTo')
    metube_url = data.get('metubeUrl')
    name_contains = data.get('nameContains')

    copied_links = main_env.fetch_season_episodes(url, username, password, metube_url, episodes_from, episodes_to,
                                       season, rd_only, name_contains)
    return jsonify(success=True, output=copied_links), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8181)
