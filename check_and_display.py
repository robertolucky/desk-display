import time
from datetime import datetime
from some_other_script import check_event  # Assuming check_event is in some_other_script.py
from display_module import display_calendar, display_art  # Assuming these functions are in display_module.py

def job():
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

# Schedule the job every 2 minutes
schedule.every(2).minutes.do(job)

# Run the scheduler in an infinite loop
while True:
    schedule.run_pending()
    time.sleep(1)