import codecs
import logging
import os
import time
from http.client import HTTPConnection
import requests
import datetime
import pytz
import json
import xml.etree.ElementTree as ET
from astral import LocationInfo
from astral.sun import sun
import humanize
import locale
from babel.dates import format_time
## Roberto's code
from PIL import Image, ImageEnhance
import cairosvg


def configure_locale():
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        logging.debug("Could not set locale")


def configure_logging():
    """
    Sets up logging with a specific logging format.
    Call this at the beginning of a script.
    Then using logging methods as normal
    """
    log_level = "INFO"
    log_format = "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
    log_dateformat = "%Y-%m-%d:%H:%M:%S"
    logging.basicConfig(level=log_level, format=log_format, datefmt=log_dateformat)
    logger = logging.getLogger()
    logger.setLevel(level=log_level)

    # Adds debug logging to python requests
    # https://stackoverflow.com/a/24588289/974369
    HTTPConnection.debuglevel = 1 if log_level == "DEBUG" else 0
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(level=log_level)
    requests_log.propagate = True

    formatter = logging.Formatter(fmt=log_format, datefmt=log_dateformat)
    handler = logger.handlers[0]
    handler.setFormatter(formatter)

def add_today_date(output_dict):
    today = datetime.datetime.now()
    # Extract year, month, and day
    year, month, day = today.year, today.month, today.day
    # Get the weekday (1=Monday, 7=Sunday)
    weekday_name = today.strftime('%A')
    output_dict['DAY_NOW']=f"{weekday_name}  -  {day}/{month}/{year}"
    
# utilize a template svg as a base for output of values
def update_svg(template_svg_filename, output_svg_filename, output_dict):
    """
    Update the `template_svg_filename` SVG.
    Replaces keys with values from `output_dict`
    Writes the output to `output_svg_filename`
    """
    # replace tags with values in SVG
    output = codecs.open(template_svg_filename, 'r', encoding='utf-8').read()

    for output_key in output_dict:
        logging.debug("update_svg() - {} -> {}"
                      .format(output_key, output_dict[output_key]))
        output = output.replace(output_key, output_dict[output_key])

    logging.debug("update_svg() - Write to SVG {}".format(output_svg_filename))

    codecs.open(output_svg_filename, 'w', encoding='utf-8').write(output)


def is_stale(filepath, ttl):
    """
    Checks if the specified `filepath` is older than the `ttl` in seconds
    Returns true if the file doesn't exist.
    """

    verdict = True
    if (os.path.isfile(filepath)):
        verdict = time.time() - os.path.getmtime(filepath) > ttl

    logging.debug(
        "is_stale({}) - {}"
        .format(filepath, str(verdict)))

    return verdict


def get_json_from_url(url, headers, cache_file_name, ttl):
    """
    Perform an HTTP GET for a `url` with optional `headers`.
    Caches the response in `cache_file_name` for `ttl` seconds.
    Returns the response as JSON
    """
    response_json = False

    if (is_stale(cache_file_name, ttl)):
        logging.info("Cache file is stale. Fetching from source.")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.text
            response_json = json.loads(response_data)
            with open(cache_file_name, 'w') as text_file:
                json.dump(response_json, text_file, indent=4)
        except Exception as error:
            logging.error(error)
            logging.error(response.text)
            logging.error(response.headers)
            raise
    else:
        logging.info("Found in cache.")
        with open(cache_file_name, 'r') as file:
            return json.loads(file.read())
    return response_json


def get_xml_from_url(url, headers, cache_file_name, ttl):
    """
    Perform an HTTP GET for a `url` with optional `headers`.
    Caches the response in `cache_file_name` for `ttl` seconds.
    Returns the response as an XML ElementTree object
    """
    logging.info(url)

    if (is_stale(cache_file_name, ttl)):
        logging.info("Cache file is stale. Fetching from source.")
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.text

            with open(cache_file_name, 'w') as text_file:
                text_file.write(response_data)
        except Exception as error:
            logging.error(error)
            logging.error(response.text)
            logging.error(response.headers)
            raise
    else:
        logging.info("Found in cache.")
        with open(cache_file_name, 'r') as file:
            response_data = file.read()
    response_xml = ET.fromstring(response_data)
    return response_xml


def get_formatted_time(dt):
    try:
        formatted_time = format_time(dt, format='short', locale=locale.getlocale()[0])
    except Exception:
        logging.debug("Locale not found for Babel library.")
        formatted_time = dt.strftime("%-I:%M %p")
    return formatted_time


def get_formatted_date(dt, include_time=True):
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    next_week = today + datetime.timedelta(days=7)
    formatter_day = "%a %b %-d"

    # Display the time in the locale format, if possible
    if include_time:
        formatted_time = get_formatted_time(dt)
    else:
        formatted_time = " "

    try:
        short_locale = locale.getlocale()[0]  # en_GB
        short_locale = short_locale.split("_")[0]  # en
        if not short_locale == "en":
            humanize.activate(short_locale)
        has_locale = True
    except Exception:
        logging.debug("Locale not found for humanize")
        has_locale = False

    if (has_locale and
            (dt.date() == today.date()
             or dt.date() == tomorrow.date()
             or dt.date() == yesterday.date())):
        # Show today/tomorrow/yesterday if available
        formatter_day = humanize.naturalday(dt.date(), "%A").title()
    elif dt.date() < next_week.date():
        # Just show the day name if it's in the next few days
        formatter_day = "%A"
    return dt.strftime(formatter_day + " " + formatted_time)



## Roberto's code

def convert_to_bmp(input_path, output_path, brightness_factor=1.5):
    """
    This function takes any image, increases its brightness,
    and converts it to a BMP format compatible with the e-ink display.     
    `brightness_factor` can be adjusted to control the brightness enhancement.

    """
    # Open the image
    img = Image.open(input_path)
    
    # Enhance the brightness of the image
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness_factor)  # Increase the brightness
    
    # Create a new black background image
    background = Image.new('RGB', (800, 480), 'white')
    
    # Calculate new size maintaining aspect ratio
    target_width = 800
    target_height = 480
    original_width, original_height = img.size
    ratio = min(target_width/original_width, target_height/original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    print(f"Resizing image to {new_width}x{new_height}")
    
    # Resize image maintaining aspect ratio
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Calculate position to center the image
    x = (800 - new_width) // 2
    y = (480 - new_height) // 2
    
    # Paste the resized image onto the black background
    background.paste(img, (x, y))
    
    # Save the image in BMP format
    background.save(output_path, format='BMP')

def convert_svg_to_png(svg_file_path, png_file_path):
    # Convert SVG to BMP using cairosvg
    cairosvg.svg2png(url=svg_file_path, write_to=png_file_path, output_width=800, output_height=480)
