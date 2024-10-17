import argparse
import configparser
import time
from urllib.parse import urlparse, parse_qs
import requests
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.utils import decode
import json


def wait(seconds):
    """
    Pause execution for the given number of seconds.

    :param seconds: Number of seconds to pause.
    """
    time.sleep(seconds)


def extract_parameters(url):
    """
    Extract path and query parameters from a URL.

    :param url: The URL to extract parameters from.
    :return: Tuple containing path parameter and query parameter.
    """
    parsed_url = urlparse(url)
    fragment = parsed_url.fragment
    fragment_url = urlparse(fragment)
    path = fragment_url.path
    query = fragment_url.query

    path_parts = path.split('/')
    path_parameter = path_parts[path_parts.index('series') + 1] if 'series' in path_parts and (
            path_parts.index('series') + 1) < len(path_parts) else None
    query_params = parse_qs(query)
    query_parameter = query_params.get('season', [None])[0]

    return path_parameter, query_parameter


def stremio_auth(username, password, driver):
    """
    Authenticate to Stremio via the web interface.

    :param username: Username for Stremio.
    :param password: Password for Stremio.
    :param driver: Selenium WebDriver instance.
    """
    login_url = "https://web.stremio.com/#/intro?form=login"
    driver.get(login_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
    email_input.send_keys(username)
    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.send_keys(password)
    login_button = driver.find_element(By.XPATH, "//div[text()='Log in']")
    login_button.click()
    WebDriverWait(driver, 10).until(EC.url_changes(login_url))


def send_to_metube(metube_url, copied_links):
    """
    Send the collected streaming links to Metube.

    :param metube_url: URL of the Metube service.
    :param copied_links: List of streaming links to send.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
        'Cookie': 'metube_theme=auto',
        'Priority': 'u=0',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }
    print("Sending to Metube...")
    for i, link in enumerate(copied_links):
        data = {
            "url": link,
            "quality": "best",
            "format": "any",
            "auto_start": True
        }
        response = requests.post(metube_url, headers=headers, json=data)
        print(f"Link {i + 1} sent", response.status_code, response.text)


def fetch_season_episodes(series_url, username, password, metube_url, epi_from, epi_to, season):
    """
    Fetch episodes from a specific season of a series.

    :param series_url: URL of the series.
    :param username: Username for Stremio authentication.
    :param password: Password for Stremio authentication.
    :param metube_url: URL of the Metube service to which links are sent.
    :param epi_from: Starting episode number to fetch.
    :param epi_to: Ending episode number to fetch.
    :param season: Specific season number to fetch episodes from.
    :return: List of copied episode streaming links.
    """
    driver = create_get_driver()
    try:
        series_url = series_url.split("?")[0]
        stremio_auth(username, password, driver)
        navigate_series(driver, series_url)
        seasons = get_number_of_seasons(driver)
        season_to_get = season if len(seasons) > 1 and season else None
        season_url = f"{series_url}?season={season_to_get}" if season_to_get else series_url
        navigate_season(driver, season_url)
        number_of_episodes = get_number_of_episodes(driver)
        path_param, season_number = extract_parameters(series_url)

        print(f"Content code detected: {path_param}")
        series_url_without_season = series_url.split("?")[0]
        copied_links = []

        if not epi_from:
            epi_from = 1
        if not epi_to:
            epi_to = number_of_episodes + 1

        for i in range(epi_from, epi_to):
            tmp_series_url = f"{series_url_without_season}/{path_param}:{season_to_get}:{i}" if season_to_get else f"{series_url_without_season}/{path_param}:{i}"
            del driver.requests
            wait(2)

            print(f"Fetching episode: {tmp_series_url}")
            driver.get(tmp_series_url)

            WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.label-container-iBMb9")))
            stream_is_rd = "RD+"
            stream_name_contains = "Judas"

            for request in driver.requests:
                download_link = None
                if "qualityfilter=" in request.url and request.response.status_code == 200:
                    body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                    data = json.loads(body.decode("utf-8"))
                    for stream in data['streams']:
                        if (not stream_is_rd or stream_is_rd in stream['name']) and (
                                not stream_name_contains or stream_name_contains in stream['title']):
                            download_link = stream['url']
                            break
                if download_link:
                    print(f"Grabbed Link: {download_link}")
                    copied_links.append(download_link)
                    break

        print("--------------------------------------")
        print("--------------------------------------")
        print("-----Bulk Print for easy copy---------")
        for (i, link) in enumerate(copied_links):
            print(link)
        print("--------------------------------------")
        print("--------------------------------------")

        if metube_url:
            send_to_metube(metube_url, copied_links)
    finally:
        driver.quit()


def get_number_of_seasons(driver):
    """
    Get the number of seasons available for the series.

    :param driver: Selenium WebDriver instance.
    :return: List of season elements.
    """
    WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.seasons-popup-label-container-fZcu4")))
    driver.find_element(By.CSS_SELECTOR, "div.seasons-popup-label-container-fZcu4").click()
    return driver.find_elements(By.CSS_SELECTOR, "div.option-SHgyE")


def get_number_of_episodes(driver):
    """
    Get the number of episodes available for the selected season.

    :param driver: Selenium WebDriver instance.
    :return: Number of episodes.
    """
    video_containers = driver.find_elements(By.CSS_SELECTOR, "div.label-container-iBMb9")
    number_of_episodes = len(video_containers)
    print(f"Detected {number_of_episodes} episodes")
    return number_of_episodes


def navigate_series(driver, series_url):
    """
    Navigate to the series page.

    :param driver: Selenium WebDriver instance.
    :param series_url: URL of the series.
    """
    driver.get(series_url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.label-container-iBMb9")))


def navigate_season(driver, url):
    """
    Navigate to the specific season page.

    :param driver: Selenium WebDriver instance.
    :param url: URL of the season page.
    """
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.label-container-iBMb9")))


def create_get_driver():
    """
    Create a Selenium WebDriver instance with specified options.

    :return: Configured Selenium WebDriver instance.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("enable-automation")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-notifications")
    return webdriver.Chrome(options=chrome_options)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_username = config['DEFAULT'].get('username', None)
    config_password = config['DEFAULT'].get('password', None)
    config_series_url = config['DEFAULT'].get('series_url', None)
    config_metube_url = config['DEFAULT'].get('metube_url', None)
    config_from = config['DEFAULT'].get('from', None)
    config_to = config['DEFAULT'].get('to', None)
    config_season = config['DEFAULT'].get('season', 1)

    parser = argparse.ArgumentParser(description='Fetch season episodes for a given series.')
    parser.add_argument('--username', type=str, help='The username for authentication')
    parser.add_argument('--password', type=str, help='The password for authentication')
    parser.add_argument('--series_url', type=str, help='The URL of the series')
    parser.add_argument('--metube_url', type=str, help='Will send download links to Metube if configured')
    args = parser.parse_args()

    username = args.username if args.username is not None else config_username
    password = args.password if args.password is not None else config_password
    series_url = args.series_url if args.series_url is not None else config_series_url
    metube_url = args.metube_url if args.metube_url is not None else config_metube_url

    fetch_season_episodes(series_url, username, password, metube_url, int(config_from), int(config_to),
                          int(config_season))