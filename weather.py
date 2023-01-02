import argparse
import json
import typing
import sys
import geocoder
from configparser import ConfigParser
from urllib import error, parse, request
from clint.textui import puts, indent, colored

BASE_WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"


def read_user_cli_args():
    """Handles user CLI interactions
    :returns argparse.Namespace: Populated namespace object
    """
    parser = argparse.ArgumentParser(
        description="gets weather and temperature information for a city."
    )
    parser.add_argument(
        "-c", "--city", nargs="+", type=str, help="enter the city name", required=False
    )
    parser.add_argument(
        "-i",
        "--imperial",
        action="store_true",
        help="display the temperature in imperial units",
    )
    return parser.parse_args()


def build_weather_query_with_city(city_input: typing.List[str], imperial: bool = False):
    """Builds the URL for an API request to OpenWeatherAPI using city name
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


def build_weather_query_with_lat_long(
    lat_long: typing.List[str], imperial: bool = False
):
    """Builds the URL for an API request to OpenWeatherAPI using lat long
    :arg
        lat_long (List[str]): List containing the lat and long
        imperial (boolean): Use imperial units for temp
    :returns
        str: URL formatted for call to OpenWeatherAPI
    """
    api_key = _get_api_key()
    units = "imperial" if imperial else "metric"
    url = (
        f"{BASE_WEATHER_API_URL}?lat={lat_long[0]}"
        f"&lon={lat_long[1]}&units={units}&appid={api_key}"
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


def get_user_current_lat_lng():
    """Gets the user's current lat long location
    :returns
        [str], list of latitude and longitude
    """
    g_location = geocoder.ip("me")
    return g_location.latlng


def weather_output_format(weather_data: dict, imperial: bool):
    """Formats the weather data for human consumption
    :returns
        str: Human readable weather report
    """
    temperature = weather_data["main"]["temp"]

    city_message = colored.blue(f"{weather_data['name']}")
    weather_description_message = colored.white(
        f"{weather_data['weather'][0]['description']}"
    )
    temperature_message = temp_color_display_format(temperature, imperial)(
        temp_display_format(temperature, imperial)
    )
    with indent(4, quote=">>>"):
        puts(f"[{city_message}]: {weather_description_message}, {temperature_message}")


def temp_display_format(temperature: str, imperial: bool):
    """Adjusts temperature display unit
    :returns
        str: Temp string with correct unit of measurement
    """
    return f"{temperature}°F" if imperial else f"{temperature}°C"


def temp_color_display_format(temperature, imperial: bool):
    """Colors corresponding to how hot or cold the temperature is
    :returns
        func(str): Function that sets the correct temp color on the string.
    """

    if imperial:
        if temperature >= 90:
            return colored.red
        elif temperature <= 50:
            return colored.cyan
        return colored.yellow
    else:
        if temperature >= 32:
            return colored.red
        elif temperature <= 10:
            return colored.cyan
        return colored.yellow


if __name__ == "__main__":
    user_args = read_user_cli_args()
    query_url = None
    if user_args.city:
        query_url = build_weather_query_with_city(user_args.city, user_args.imperial)
    else:
        current_location = get_user_current_lat_lng()
        query_url = build_weather_query_with_lat_long(
            current_location, user_args.imperial
        )

    weather_data = get_weather_data(query_url)
    weather_output_format(weather_data, user_args.imperial)
