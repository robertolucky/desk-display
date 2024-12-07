import time
from utility import convert_to_bmp
from artic_api import artic_download
from e_paper import e_paper_display
from calendar_api import event_manager
# once per day
title, artist =artic_download.download_image("art_image")
convert_to_bmp("art_image.jpg","art_image.bpm")
e_paper_display("art_image.bpm")
event_manager.push_event(f"Title: {title}, artist: {artist}")
'''
# Call the check_event function and get the time of the first event
first_event_time = check_event()

# Get the current time
current_time = datetime.now()

# Calculate the difference in minutes between the current time and the first event time
time_difference = (first_event_time - current_time).total_seconds() / 60.0

# Check if the next event is less than 10 minutes away
if time_difference < 10:
    display_calendar()
else:
    display_art()

'''
