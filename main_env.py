import argparse
import configparser
import time
import os  # Importing os module
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
    :param seconds: The number of seconds for the function to pause execution.
    :return: None
    """
    time.sleep(seconds)


def extract_parameters(url):
    """
    :param url: The URL containing the fragment to be parsed.
    :return: A tuple containing path_parameter and query_parameter.
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
    :param username: The username of the Stremio account.
    :param password: The password of the Stremio account.
    :param driver: The Selenium WebDriver instance used for automating browser actions.
    :return: None
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



def fetch_season_episodes(series_url, username, password, epi_from, epi_to, season, is_rd, name_contains):
    """
    :param series_url: URL of the series page to fetch episodes from.
    :param username: Username for authentication.
    :param password: Password for authentication.
    :param epi_from: Starting episode number to fetch.
    :param epi_to: Ending episode number to fetch.
    :param season: Specific season number to fetch episodes from.
    :param is_rd: Flag to filter streams for RD+.
    :param name_contains: String to filter stream names containing this substring.
    :return: List of direct links to the fetched episodes.
    """
    driver = create_get_driver()
    try:
        print("Processing...")
        series_url = series_url.split("?")[0]
        stremio_auth(username, password, driver)
        navigate_series(driver, series_url)
        seasons = get_number_of_seasons(driver)
        season_to_get = season if len(seasons) > 1 and season else None
        navigate_season(driver, series_url, season_to_get)
        number_of_episodes = get_number_of_episodes(driver)
        path_param, season_number = extract_parameters(series_url)
        print(f"Content code detected: {path_param}")
        series_url_without_season = series_url.split("?")[0]
        copied_links = []
        if not epi_from:
            epi_from = 1
        if not epi_to:
            epi_to = number_of_episodes + 1
        for i in range(int(epi_from), int(epi_to + 1)):
            tmp_series_url = f"{series_url_without_season}/{path_param}:{season_to_get}:{i}" if season_to_get else f"{series_url_without_season}/{path_param}:{i}"
            del driver.requests
            wait(1)
            print(f"S{season_to_get}:E{i}", "..")
            # print(f"Fetching episode: {tmp_series_url}")
            driver.get(tmp_series_url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.label-container-iBMb9")))
            wait(2)
            stream_is_rd = None
            stream_name_contains = None
            if is_rd:
                stream_is_rd = "RD+"
            if name_contains:
                stream_name_contains = name_contains
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
    finally:
        driver.quit()
    return copied_links


def get_number_of_seasons(driver):
    """
    :param driver: WebDriver instance used to interact with the browser.
    :return: List of WebElements representing the number of seasons.
    """
    WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.seasons-popup-label-container-fZcu4")))
    driver.find_element(By.CSS_SELECTOR, "div.seasons-popup-label-container-fZcu4").click()
    return driver.find_elements(By.CSS_SELECTOR, "div.option-SHgyE")


def get_number_of_episodes(driver):
    """
    :param driver: The web driver instance used to interact with the web page.
    :return: The number of unique episodes detected on the page.
    """
    video_containers = driver.find_elements(By.CSS_SELECTOR, "div.label-container-iBMb9")
    unique_episodes = []
    for (container_index, container) in enumerate(video_containers):
        if not container.text == "":
            unique_episodes.append(container)
    print(f"Detected {len(unique_episodes)} episodes")
    return len(unique_episodes)


def navigate_series(driver, series_url):
    """
    :param driver: The Selenium WebDriver instance used to navigate the browser.
    :param series_url: The URL of the series page to navigate to.
    :return: None
    """
    driver.get(series_url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.label-container-iBMb9")))


def navigate_season(driver, series_url, season_to_get):
    """
    :param driver: The WebDriver instance used to navigate the web page.
    :param series_url: The URL of the series page to navigate to.
    :param season_to_get: The specific season number to navigate, can be None to navigate to the default series page.
    :return: None
    """
    print(f"Season: {season_to_get}")
    url = f"{series_url}?season={season_to_get}" if season_to_get else series_url
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.label-container-iBMb9")))


def create_get_driver():
    """
    Creates and configures a Chrome WebDriver instance with specific options for a headless, automated browser session.

    The configurations include disabling the GPU, running no sandbox mode, enabling automation, and various other settings to ensure stable headless browser operations and security handling.

    :return: A configured instance of Chrome WebDriver
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


def print_for_bash_pipe():
    global i, link
    print("--------------------------------------")
    print("-----Bulk Print for pattern pipe---------")
    print("-----eg Bash: grep '^$pattern' '$input_file' | sed 's/^$pattern//'---------")
    for (i, link) in enumerate(copied_links):
        print(f"@@##@@{link}")
    print("--------------------------------------")


def print_for_easy_copy():
    global i, link
    print("--------------------------------------")
    print("-----Bulk Print for easy copy---------")
    for (i, link) in enumerate(copied_links):
        print(f"{link}")
    print("--------------------------------------")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    username = os.getenv('USERNAME', None)
    password = os.getenv('PASSWORD', None)
    series_url = os.getenv('SERIES_URL', None)
    epi_from = os.getenv('FROM', 1)
    epi_to = os.getenv('TO', None)
    season = os.getenv('SEASON', 1)
    is_rd = os.getenv('IS_RD', None)
    name_contains = os.getenv('NAME_CONTAINS', None)

    copied_links = fetch_season_episodes(
        series_url,
        username,
        password,
        int(epi_from) if epi_from else None,
        int(epi_to) if epi_to else None,
        int(season) if season else 1,
        is_rd,
        name_contains
    )

    # print_for_bash_pipe()
    print_for_easy_copy()



