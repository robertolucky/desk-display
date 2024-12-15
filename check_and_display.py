import os
import json
from datetime import datetime, timedelta, timezone
from utility import convert_to_bmp, convert_svg_to_png
from artic_api import artic_download
from e_paper.e_paper_display import display_image
from calendar_api import event_manager

dir_path = os.path.dirname(os.path.realpath(__file__))
art_image_path_jpg = os.path.join(dir_path, 'art_image.jpg')
art_image_path_bpm = os.path.join(dir_path, 'art_image.bpm')
calendar_path_svg = os.path.join(dir_path, 'calendar_screen.svg')
calendar_path_png = os.path.join(dir_path, 'calendar_screen.png')
FLAGS_FILE_PATH = os.path.join(dir_path, 'flags.json')

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

def download_image_if_needed():
    # Check if the image has already been downloaded today
    if get_flag("image_downloaded"):
        return False  # Image has been downloaded, do nothing

    # Download the image
    title, artist = artic_download.download_image("art_image")
    convert_to_bmp(art_image_path_jpg,art_image_path_bpm)
    set_flag("image_downloaded", True)
    set_flag("art_in_show", False)
    event_manager.push_event(f"Art of the day - Title: {title}, artist: {artist}")
    return True

def display():
    if get_flag("art_in_show") and get_flag("time_for_meeting"):
        display_image(calendar_path_png)
        set_flag("art_in_show", False)

    elif (not get_flag("art_in_show")) and (not get_flag("time_for_meeting")):
        display_image(art_image_path_bpm)
        set_flag("art_in_show", True)

if __name__ == "__main__":
    reset_flag_daily()
    download_image_if_needed()

    first_event,control_code=event_manager.update_and_return()
    convert_svg_to_png(calendar_path_svg, calendar_path_png)

    if control_code==1:
        set_flag("image_downloaded", False)

    if first_event:  # Ensure first_event is not None or empty
        # Calculate the time difference in minutes
        time_difference = (first_event - datetime.now(timezone.utc)).total_seconds() / 60.0
        #print(f" First event time: {first_event},  date now = {datetime.now(timezone.utc)}")
        #print(time_difference)

        # Check if the current time is within 10 minutes before or 5 minutes after the event
        if -10 <= time_difference <= 5:
            set_flag("time_for_meeting", True)
        else:
            set_flag("time_for_meeting", False)

    display()
