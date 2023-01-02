import argparse
import json
import typing
import sys
from configparser import ConfigParser
from urllib import error, parse, request

BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"


def read_user_cli_args():
    """Handles user CLI interactions
    :returns argparse.Namespace: Populated namespace object
    """
    parser = argparse.ArgumentParser(
        description="gets weather and temperature information for a city."
    )
    parser.add_argument("city", nargs="+", type=str, help="enter the city name")
    parser.add_argument(
        "-i",
        "--imperial",
        action="store_true",
        help="display the temperature in imperial units",
    )
    return parser.parse_args()


def build_weather_query(city_input: typing.List[str], imperial: bool = False):
    """Builds the URL for an API request to OpenWeatherAPI
    Args:
        city_input (List[str]): Name of city
        imperial (boolean): Use imperial units for temp
    Returns:
        str: URL formatted for call to OpenWeatherAPI
    """
    api_key = _get_api_key()
    city_name = " ".join(city_input)
    url_encoded_city_name = parse.quote_plus(city_name)
    units = "imperial" if imperial else "metric"
    url = (
        f"{BASE_WEATHER_API_URL}?q={url_encoded_city_name}"
        f"&units={units}&appid={api_key}"
    )
    return url


def get_weather_data(query_url: str):
    """Makes API request to OpenWeatherAPI
    Args:
        query_url [str]: URL formatted for OpenWeather's API
    Returns:
        dict: Weather Information
    """
    try:
        response = request.urlopen(query_url)
    except error.HTTPError as http_error:
        if http_error.code == 401:
            sys.exit("Access denied. Check API key.")
        elif http_error.code == 404:
            sys.exit("Can't find weather data for this city.")
        else:
            sys.exit(f"Something went wrong... ({http_error.code}")

    data = response.read()

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        sys.exit("Couldn't read server response.")


def _get_api_key():
    """Fetch the api_key from the configuration file"""
    config = ConfigParser()
    config.read("secrets.ini")
    return config["openweather"]["api_key"]


if __name__ == "__main__":
    user_args = read_user_cli_args()
    query_url = build_weather_query(user_args.city, user_args.imperial)
    weather_data = get_weather_data(query_url)
    print(
        f"{weather_data['name']}:"
        f"{weather_data['weather'][0]['description']}"
        f"({weather_data['main']['temp']})"
    )
