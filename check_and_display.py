import os
import sys
import json
import random
import fcntl
import pytz
import logging

from datetime import datetime, timezone
from utility import convert_to_bmp, convert_svg_to_png
from artic_api import artic_download
from e_paper.e_paper_display import display_image
from calendar_api import event_manager

LOCK_FILE = "/tmp/desk_display.lock"

# Acquire an OS-level lock. Unlike the old "check if file exists" approach,
# flock is atomic AND is released automatically when the process dies,
# so a crash can never leave a stale lock behind, and two overlapping
# cron runs can never execute concurrently (the cause of the duplicate
# "Art of the day" events).
_lock_fd = open(LOCK_FILE, "w")
try:
    fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("Another instance of the script is running.")
    sys.exit(0)

dir_path = os.path.dirname(__file__)
art_image_path_jpg = os.path.join(dir_path, 'artic_api/art_image.jpg')
art_image_path_bmp = os.path.join(dir_path, 'artic_api/art_image.bmp')
calendar_path_svg = os.path.join(dir_path, 'calendar_api/calendar_screen.svg')
calendar_path_png = os.path.join(dir_path, 'calendar_api/calendar_screen.png')
personal_photos_dir = os.path.join(dir_path, 'personal_photos')
FLAGS_FILE_PATH = os.path.join(dir_path, 'flags.json')
BRUSSELS_TIMEZONE = pytz.timezone('Europe/Brussels')


def _load_flags():
    if os.path.exists(FLAGS_FILE_PATH):
        try:
            with open(FLAGS_FILE_PATH, 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            logging.warning("flags.json unreadable/corrupt, starting fresh")
    return {}


def get_flag(flag_name):
    return _load_flags().get(flag_name, False)


def set_flag(flag_name, value):
    flags = _load_flags()
    flags[flag_name] = value
    # Atomic write: write to a temp file then rename. A crash mid-write
    # can no longer corrupt flags.json.
    tmp_path = FLAGS_FILE_PATH + ".tmp"
    with open(tmp_path, 'w') as file:
        json.dump(flags, file, indent=4)
    os.replace(tmp_path, FLAGS_FILE_PATH)


def reset_flag_daily():
    if os.path.exists(art_image_path_jpg):
        last_modified_time = os.path.getmtime(art_image_path_jpg)
        last_modified_date = datetime.fromtimestamp(last_modified_time).date()
        if last_modified_date < datetime.now().date():
            set_flag("image_downloaded", False)
            logging.info("Image date is old, finding a new one..")
    else:
        set_flag("image_downloaded", False)


def download_image_if_needed():
    if get_flag("image_downloaded"):
        return False

    result = artic_download.download_image()
    if result is None:
        # Download failed; leave the flag False so the next cron run retries.
        logging.error("Art download failed, will retry on next run")
        return False

    title, artist = result
    convert_to_bmp(art_image_path_jpg, art_image_path_bmp)
    set_flag("image_downloaded", True)
    set_flag("art_in_show", False)
    # push_event now deduplicates server-side, so even if something goes
    # wrong here at most one event per artwork can exist.
    event_manager.push_event(f"Art of the day - Title: {title}, artist: {artist}")
    return True


def display():
    if get_flag("art_in_show") and get_flag("time_for_meeting"):
        if display_image(calendar_path_png):
            set_flag("art_in_show", False)
    elif (not get_flag("art_in_show")) and (not get_flag("time_for_meeting")):
        if display_image(art_image_path_bmp):
            set_flag("art_in_show", True)
    else:
        logging.info("Nothing to display")


if __name__ == "__main__":
    reset_flag_daily()
    download_image_if_needed()

    first_event, control_code = event_manager.update_and_return()
    convert_svg_to_png(calendar_path_svg, calendar_path_png)

    if control_code == 1:
        set_flag("image_downloaded", False)
        set_flag("art_in_show", False)

    if control_code == 2:
        if os.path.isdir(personal_photos_dir):
            image_files = [f for f in os.listdir(personal_photos_dir)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
                           and f != 'photo.bmp']
            if image_files:
                random_image_path = os.path.join(personal_photos_dir, random.choice(image_files))
                random_image_bmp_path = os.path.join(personal_photos_dir, 'photo.bmp')
                convert_to_bmp(random_image_path, random_image_bmp_path, 1)
                if display_image(random_image_bmp_path):
                    set_flag("art_in_show", True)
            else:
                logging.warning("No images found in personal_photos/")
        else:
            logging.warning("personal_photos/ directory does not exist")

    if first_event:
        first_event = (BRUSSELS_TIMEZONE.localize(first_event)
                       if first_event.tzinfo is None
                       else first_event.astimezone(BRUSSELS_TIMEZONE))
        current_time_brussels = datetime.now(timezone.utc).astimezone(BRUSSELS_TIMEZONE)
        time_difference = (first_event - current_time_brussels).total_seconds() / 60.0
        logging.info(f"Next event is at {first_event} in {time_difference:.1f} min")
        set_flag("time_for_meeting", -5 <= time_difference <= 15)
    else:
        set_flag("time_for_meeting", False)

    display()
