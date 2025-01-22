import os
import sys
import socket
from e_paper.e_paper_display import display_text

LOCK_FILE = "/tmp/my_script.lock"

# Check if the lock file exists
if os.path.exists(LOCK_FILE):
    print("Another instance of the script is running.")
    sys.exit(1)

# Create a lock file to prevent other instances from running
with open(LOCK_FILE, 'w') as lock_file:
    lock_file.write("")



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

address=get_ip_address()
print(f"The IP address of the Raspberry Pi is: {address}")
if not display_text(address):
    display_text(address)
# Remove the lock file when done
os.remove(LOCK_FILE)