import os
import sys
import json
import random
import pytz

from datetime import datetime, timedelta, timezone
from utility import convert_to_bmp, convert_svg_to_png
from artic_api import artic_download
from e_paper.e_paper_display import display_image
from calendar_api import event_manager
import logging

LOCK_FILE = "/tmp/my_script.lock"

# Check if the lock file exists
if os.path.exists(LOCK_FILE):
    print("Another instance of the script is running.")
    sys.exit(1)

# Create a lock file to prevent other instances from running
with open(LOCK_FILE, 'w') as lock_file:
    lock_file.write("")

dir_path = os.path.dirname(os.path.realpath(__file__))
art_image_path_jpg = os.path.join(dir_path, 'artic_api/art_image.jpg')
art_image_path_bpm = os.path.join(dir_path, 'artic_api/art_image.bpm')
calendar_path_svg = os.path.join(dir_path, 'calendar_api/calendar_screen.svg')
calendar_path_png = os.path.join(dir_path, 'calendar_api/calendar_screen.png')
personal_pic_jpg = os.path.join(dir_path, 'personal_photos/me_and_fra.jpg')
personal_pic_bmp = os.path.join(dir_path, 'personal_photos/me_and_fra.bpm')
FLAGS_FILE_PATH = os.path.join(dir_path, 'flags.json')
BRUSSELS_TIMEZONE = pytz.timezone('Europe/Brussels')

def get_flag(flag_name):
    if os.path.exists(FLAGS_FILE_PATH):
        with open(FLAGS_FILE_PATH, 'r') as file:
            flags = json.load(file)
            return flags.get(flag_name, False)
    return False

def set_flag(flag_name, value):
    if os.path.exists(FLAGS_FILE_PATH):
        with open(FLAGS_FILE_PATH, 'r') as file:
            flags = json.load(file)
    else:
        flags = {}
    flags[flag_name] = value
    with open(FLAGS_FILE_PATH, 'w') as file:
        json.dump(flags, file, indent=4)

def reset_flag_daily():
    # Check if the image file exists
    if os.path.exists(art_image_path_jpg):
        # Get the last modified time of the image file
        last_modified_time = os.path.getmtime(art_image_path_jpg)
        last_modified_date = datetime.fromtimestamp(last_modified_time).date()
        current_date = datetime.now().date()

        # If the image is from yesterday or older, reset the flag
        if last_modified_date < current_date:
            set_flag("image_downloaded", False)
            logging.info("Image date is old, finding a new one..")
    else:
        set_flag("image_downloaded", False)




def download_image_if_needed():
    # Check if the image has already been downloaded today
    if get_flag("image_downloaded"):
        return False  # Image has been downloaded, do nothing
    
    # Download the image
    title, artist = artic_download.download_image()
    convert_to_bmp(art_image_path_jpg,art_image_path_bpm)
    set_flag("image_downloaded", True)
    set_flag("art_in_show", False)
    event_manager.push_event(f"Art of the day - Title: {title}, artist: {artist}")
    return True

def display():
    if get_flag("art_in_show") and get_flag("time_for_meeting"):
        if display_image(calendar_path_png):
            set_flag("art_in_show", False)

    elif (not get_flag("art_in_show")) and (not get_flag("time_for_meeting")):
        if display_image(random_image_bmp_path):
            set_flag("art_in_show",True)
    else:
        logging.info("Nothing to display")

if __name__ == "__main__":
    reset_flag_daily()
    download_image_if_needed()

    first_event,control_code=event_manager.update_and_return()
    convert_svg_to_png(calendar_path_svg, calendar_path_png)
    
    if control_code==1:
        set_flag("image_downloaded", False)
        set_flag("art_in_show",False)

    if control_code==2:
        # List all files in the 'personal_photos' directory
        personal_photos = os.listdir(os.path.join(dir_path, 'personal_photos'))
        # Filter for image files, assuming they are .jpg or .bmp
        image_files = [file for file in personal_photos if file.endswith(('.jpg', '.bmp'))]
        # Choose a random image file
        random_image = random.choice(image_files)
        # Create the full path for the randomly selected image
        random_image_path = os.path.join(dir_path, 'personal_photos', random_image)
        # Convert to bmp if necessary (assuming all images need to be in .bmp format for display)
        random_image_bmp_path = os.path.join(dir_path, 'personal_photos/photo.bmp')
        convert_to_bmp(random_image_path, random_image_bmp_path,1)
        # Display the random image
        if display_image(random_image_bmp_path):
            set_flag("art_in_show",True)
    

    if first_event:  # Ensure first_event is not None or empty
        # Convert first_event to Brussels timezone before the comparison
        first_event = BRUSSELS_TIMEZONE.localize(first_event) if first_event.tzinfo is None else first_event.astimezone(BRUSSELS_TIMEZONE)
        # Also convert the current time to Brussels timezone
        current_time_brussels = datetime.now(timezone.utc).astimezone(BRUSSELS_TIMEZONE)
        # Calculate the time difference in minutes
        time_difference = (first_event - current_time_brussels).total_seconds() / 60.0
        logging.info(f"Next event is at {first_event} in {time_difference}")

        # Check if the current time is within 15 minutes before or 5 minutes after the event
        if -5 <= time_difference <= 15:
            set_flag("time_for_meeting", True)
        else:
            set_flag("time_for_meeting", False)

    display()
    # Remove the lock file when done
    os.remove(LOCK_FILE)