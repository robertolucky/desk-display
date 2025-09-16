import datetime
import os.path
import os
import logging
from xml.sax.saxutils import escape
from calendar_api.base_provider import CalendarEvent
from calendar_api.google import GoogleCalendar 
from utility import get_formatted_time, update_svg, configure_logging, get_formatted_date, configure_locale, add_today_date

configure_locale()
configure_logging()

# note: increasing this will require updates to the SVG template to accommodate more events
max_event_results =  6
google_calendar_id = "robertolacom.rlc@gmail.com"
google_calendar_id = "roberto.lacommare@pickit3d.com"
ttl = 300
fake_event_h=7
dir_path = os.path.dirname(os.path.realpath(__file__))
template_svg_filename = os.path.join(dir_path, 'screen-temp-rob.svg')
output_svg_filename = os.path.join(dir_path, 'calendar_screen.svg')

def get_formatted_calendar_events(fetched_events: list[CalendarEvent], skip_all_day_events: bool = True) -> dict:
    formatted_events = {}
    event_index = 0  # Index to iterate over fetched_events
    formatted_event_count = 0  # Counter for the number of events formatted

    while formatted_event_count < max_event_results and event_index < len(fetched_events):
        event = fetched_events[event_index]
        event_index += 1

        if skip_all_day_events and event.all_day_event:
            continue

        formatted_event_count += 1
        event_label_id = str(formatted_event_count)
        formatted_events['CAL_DATETIME_' + event_label_id] = get_datetime_formatted(event.start, event.end, event.all_day_event)
        formatted_events['CAL_DATETIME_START_' + event_label_id] = get_datetime_formatted(event.start, event.end, event.all_day_event, True)
        formatted_events['CAL_DESC_' + event_label_id] = event.summary

    # Fill in the remaining slots with empty strings if there are fewer events than max_event_results
    for index in range(formatted_event_count, max_event_results):
        event_label_id = str(index + 1)
        formatted_events['CAL_DATETIME_' + event_label_id] = ""
        formatted_events['CAL_DESC_' + event_label_id] = ""

    return formatted_events


def get_datetime_formatted(event_start, event_end, is_all_day_event, start_only=False):

    if is_all_day_event or type(event_start) == datetime.date:
        start = datetime.datetime.combine(event_start, datetime.time.min)
        end = datetime.datetime.combine(event_end, datetime.time.min)

        start_day = get_formatted_date(start, include_time=False)
        end_day = get_formatted_date(end, include_time=False)
        if start == end:
            day = start_day
        else:
            day = "{} - {}".format(start_day, end_day)
    elif type(event_start) == datetime.datetime:
        start_date = event_start
        end_date = event_end
        if start_date.date() == end_date.date():
            start_formatted = get_formatted_date(start_date)
            end_formatted = get_formatted_time(end_date)
        else:
            start_formatted = get_formatted_date(start_date)
            end_formatted = get_formatted_date(end_date)
        day = start_formatted if start_only else "{} - {}".format(start_formatted, end_formatted)
    else:
        day = ''
    return day

def init_calendar():
    today_start_time = datetime.datetime.utcnow()+ datetime.timedelta(minutes=40)

    oneweeklater_iso = (datetime.datetime.now()
                        + datetime.timedelta(days=7))

    logging.info("Fetching Google Calendar Events")
    provider = GoogleCalendar(google_calendar_id, max_event_results, today_start_time, oneweeklater_iso)
    return provider

def push_event(message="ignore this event"):
    start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(fake_event_h, 0))
    end_time = datetime.datetime.combine(datetime.date.today(), datetime.time(fake_event_h, 15))
    provider=init_calendar()
    reminders_override = {
        'useDefault': False,
        'overrides': []
    }
    provider.create_event(message, start_time, end_time)


def update_and_return():
    provider = init_calendar()
    calendar_events = provider.get_calendar_events()
    
    # Filter out events that start with "Art of the day"
    calendar_events = [event for event in calendar_events if not event.summary.startswith("Art of the day")]
     # Filter out all-day events
    non_all_day_events = [event for event in calendar_events if not event.all_day_event]
    
    # Get the start of the first non-all-day event, if there is one
    first_event = non_all_day_events[0].start if non_all_day_events else None

    output_dict = get_formatted_calendar_events(calendar_events)
    add_today_date(output_dict)
    
    # XML escape for safety
    for key, value in output_dict.items():
        output_dict[key] = escape(value)
    
    # Extract control value if an event starts with "Display code:"
    control_value = None
    for event in calendar_events:
        if event.summary.startswith("Display code:"):
            try:
                control_value = int(event.summary.split("Display code:")[1].strip())
                logging.info(f"Found a control code:{control_value}")
                provider.delete_event_by_summary("Display code")
                break  # Assuming only one event contains the control value
            except ValueError:
                logging.warning("Invalid control value format in event summary")
                control_value = None
    
    logging.info("Updating SVG")
    update_svg(template_svg_filename, output_svg_filename, output_dict)
    return first_event, control_value

if __name__ == "__main__":
    print(update_and_return())
