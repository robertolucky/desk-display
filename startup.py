import os
import sys
import socket
import json
import time
from e_paper.e_paper_display import display_text

LOCK_FILE = "/tmp/my_script.lock"
FLAGS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'flags.json')

# Create a lock file to prevent other instances from running
with open(LOCK_FILE, 'w') as lock_file:
    lock_file.write("")

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
# Remove the lock file when done
os.remove(LOCK_FILE)
