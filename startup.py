import os
import sys
import socket
import json
import time
import fcntl
from e_paper.e_paper_display import display_text

LOCK_FILE = "/tmp/desk_display.lock"
FLAGS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'flags.json')

# Hold the same flock as check_and_display.py while starting up.
# flock is released automatically when this process exits (even on crash),
# so it can never permanently block the cron script like the old
# "create a file and hope we delete it" approach could.
_lock_fd = open(LOCK_FILE, 'w')
fcntl.flock(_lock_fd, fcntl.LOCK_EX)

time.sleep(30)

def get_ip_address():
    # Create a dummy socket to connect to an external server
    try:
        # Connect to Google's DNS server as an example
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
    except Exception as e:
        ip_address = "Unable to determine IP Address: " + str(e)
    return ip_address

message=f"The IP address is: {get_ip_address()}"
print(message)
if not display_text(message):
    display_text(message)

# Reset the flags to a starting point
with open(FLAGS_FILE_PATH, 'w') as file:
    json.dump({
    "image_downloaded": False,
    "art_in_show": False,
    "time_for_meeting": False
    }, file, indent=4)
# flock released automatically on exit
