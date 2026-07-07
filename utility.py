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

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

# The EXACT 7-color palette the panel uses (see e_paper/epd7in3f.py getbuffer).
# Dithering against this same palette here means what we render is exactly what
# the panel shows - the driver's own quantize pass becomes a no-op.
PANEL_PALETTE = (
    0, 0, 0,        # black
    255, 255, 255,  # white
    0, 255, 0,      # green
    0, 0, 255,      # blue
    255, 0, 0,      # red
    255, 255, 0,    # yellow
    255, 128, 0,    # orange
)
PANEL_W, PANEL_H = 800, 480


def _panel_palette_image():
    pal = Image.new("P", (1, 1))
    pal.putpalette(PANEL_PALETTE + (0, 0, 0) * 249)
    return pal


def _load_caption_font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        os.path.join(os.path.dirname(__file__), "e_paper", "Font.ttc"),
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_caption(canvas, title, artist):
    """Draw a translucent strip along the bottom with the artwork title/artist.
    Returns an RGBA canvas with the caption composited on, or None if nothing
    to draw."""
    title = (title or "").strip()
    artist = (artist or "").strip()
    if not title and not artist:
        return None
    text = title if not artist else "{}  -  {}".format(title, artist)

    draw = ImageDraw.Draw(canvas)
    font_size = 22
    font = _load_caption_font(font_size)
    while font_size > 12 and draw.textlength(text, font=font) > PANEL_W - 24:
        font_size -= 2
        font = _load_caption_font(font_size)
    if draw.textlength(text, font=font) > PANEL_W - 24:
        while text and draw.textlength(text + "\u2026", font=font) > PANEL_W - 24:
            text = text[:-1]
        text += "\u2026"

    bbox = draw.textbbox((0, 0), text, font=font)
    strip_h = (bbox[3] - bbox[1]) + 16
    canvas = canvas.convert("RGBA")
    strip = Image.new("RGBA", (PANEL_W, strip_h), (0, 0, 0, 180))
    canvas.alpha_composite(strip, (0, PANEL_H - strip_h))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, PANEL_H - strip_h + 8 - bbox[1]), text, font=font,
              fill=(255, 255, 255, 255))
    return canvas


PANEL_AR = PANEL_W / PANEL_H  # 1.667


def _fit_to_panel(img, crop_tolerance=0.20, top_bias=0.30):
    """Place `img` onto the 800x480 panel.

    - If the aspect ratio is within `crop_tolerance` of the panel's, crop to
      fill (no white bars). For portrait-ish images the crop is biased toward
      the top (top_bias) so faces/heads near the top aren't cut off.
    - If the aspect ratio differs strongly (tall portraits, panoramas), the
      whole image is letterboxed on a white background so nothing is lost.
    """
    ar = img.width / img.height
    mismatch = abs(ar - PANEL_AR) / PANEL_AR
    if mismatch <= crop_tolerance:
        centering = (0.5, top_bias if ar < PANEL_AR else 0.5)
        return ImageOps.fit(img, (PANEL_W, PANEL_H),
                            method=Image.Resampling.LANCZOS, centering=centering)
    canvas = Image.new("RGB", (PANEL_W, PANEL_H), "white")
    ratio = min(PANEL_W / img.width, PANEL_H / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    canvas.paste(resized, ((PANEL_W - new_size[0]) // 2, (PANEL_H - new_size[1]) // 2))
    return canvas


def convert_to_bmp(input_path, output_path, brightness_factor=1.15,
                   saturation_factor=1.50, mode="art", title="", artist=""):
    """Prepare an image for the 7-color ACeP e-paper panel.

    mode="art"       -> aspect-aware fit + caption strip + dithering
    mode="photo" / 1 -> aspect-aware fit, no caption + dithering
    mode="letterbox" -> always letterbox on white + dithering
    mode="crop"      -> always crop to fill (top-biased) + dithering

    "art"/"photo" crop only when the aspect ratio is close to the panel's,
    otherwise they letterbox so portraits aren't decapitated.

    An int in the `mode` position is treated as photo mode, so old calls like
    convert_to_bmp(a, b, 1) keep working.
    """
    if isinstance(mode, int):
        mode = "photo"

    img = Image.open(input_path).convert("RGB")
    # Gentle enhancement: pushing saturation hard before dithering forces pixels
    # to the palette extremes and makes the 7-color output look garish/noisy.
    img = ImageEnhance.Brightness(img).enhance(brightness_factor)
    img = ImageEnhance.Color(img).enhance(saturation_factor)

    if mode == "letterbox":
        canvas = _fit_to_panel(img, crop_tolerance=0.0)      # always letterbox
    elif mode == "crop":
        canvas = _fit_to_panel(img, crop_tolerance=1.0)      # always crop
    else:
        canvas = _fit_to_panel(img)                          # decide per aspect

    if mode == "art":
        composited = _draw_caption(canvas, title, artist)
        if composited is not None:
            canvas = composited.convert("RGB")

    # Floyd-Steinberg dithering against the panel's exact palette, so smooth
    # gradients don't posterize into flat color bands.
    dithered = canvas.quantize(palette=_panel_palette_image(),
                               dither=Image.Dither.FLOYDSTEINBERG).convert("RGB")
    dithered.save(output_path, format="BMP")


def convert_svg_to_png(svg_file_path, png_file_path):
    # Convert SVG to PNG using cairosvg
    cairosvg.svg2png(url=svg_file_path, write_to=png_file_path, output_width=800, output_height=480)
