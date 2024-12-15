import datetime
from calendar_api.base_provider import BaseCalendarProvider, CalendarEvent
from utility import is_stale
import os
import logging
import pickle
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ttl = float(os.getenv("CALENDAR_TTL", 1 * 60 * 60))
google_calendar_timezone = os.getenv("GOOGLE_CALENDAR_TIME_ZONE_NAME", 'Europe/Brussels')
dir_path = os.path.dirname(os.path.realpath(__file__))
google_credentials_json = os.path.join(dir_path, 'credentials.json')
google_token_pickle = os.path.join(dir_path, 'token.pickle')
google_calendar_pickle =  os.path.join(dir_path,'cache_calendar.pickle')

class GoogleCalendar(BaseCalendarProvider):
    def __init__(self, google_calendar_id, max_event_results, from_date, to_date):
        self.max_event_results = max_event_results
        self.from_date = from_date
        self.to_date = to_date
        self.google_calendar_id = google_calendar_id

    def get_google_credentials(self):
        google_api_scopes = ['https://www.googleapis.com/auth/calendar']#.readonly']

        credentials = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(google_token_pickle):
            with open(google_token_pickle, 'rb') as token:
                credentials = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    google_credentials_json, google_api_scopes)
                credentials = flow.run_local_server()
            # Save the credentials for the next run
            with open(google_token_pickle, 'wb') as token:
                pickle.dump(credentials, token)

        return credentials

    def get_calendar_events(self) -> list[CalendarEvent]:
        calendar_events = []

        service = build('calendar', 'v3', credentials=self.get_google_credentials(), cache_discovery=False)

        events_result = None

        if is_stale(os.getcwd() + "/" + google_calendar_pickle, ttl):
            logging.debug("Pickle is stale, calling the Calendar API")

            # Call the Calendar API
            events_result = service.events().list(
                calendarId=self.google_calendar_id,
                timeMin=self.from_date.isoformat() + 'Z',
                timeZone=google_calendar_timezone,
                maxResults=self.max_event_results,
                singleEvents=True,
                orderBy='startTime').execute()

            for event in events_result.get('items', []):
                if event['start'].get('date'):
                    is_all_day = True
                    start_date = datetime.datetime.strptime(event['start'].get('date'), "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(event['end'].get('date'), "%Y-%m-%d")
                    # Google Calendar marks the 'end' of all-day-events as
                    # the day _after_ the last day. eg, Today's all day event ends tomorrow!
                    # So subtract a day
                    end_date = end_date - datetime.timedelta(days=1)
                else:
                    is_all_day = False
                    start_date = datetime.datetime.strptime(event['start'].get('dateTime'), "%Y-%m-%dT%H:%M:%S%z")
                    end_date = datetime.datetime.strptime(event['end'].get('dateTime'), "%Y-%m-%dT%H:%M:%S%z")

                summary = event['summary']
                event_id = event['id']  # Get the event ID from the event dictionary
                event_organizer = event['creator']['email']
                calendar_events.append(CalendarEvent(event_id, summary, start_date, end_date, is_all_day, event_organizer))

            with open(google_calendar_pickle, 'wb') as cal:
                pickle.dump(calendar_events, cal)

        else:
            logging.info("Found in cache")
            with open(google_calendar_pickle, 'rb') as cal:
                calendar_events = pickle.load(cal)

        if len(calendar_events) == 0:
            logging.info("No upcoming events found.")

        return calendar_events


    def create_event(self, event_name: str, start_time: datetime.datetime, end_time: datetime.datetime):
        service = build('calendar', 'v3', credentials=self.get_google_credentials(), cache_discovery=False)

        # Determine timezone to be used
        time_zone = google_calendar_timezone or 'UTC'  # Default to UTC if no timezone is set

        # Ensure start_time and end_time are aware datetime objects
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=pytz.timezone(time_zone))
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=pytz.timezone(time_zone))

        event = {
            'summary': event_name,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': time_zone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': time_zone,
            },
        }

        event = service.events().insert(calendarId=self.google_calendar_id, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    
    def delete_event(self, event_id: str):
        service = build('calendar', 'v3', credentials=self.get_google_credentials(), cache_discovery=False)
        try:
            service.events().delete(calendarId=self.google_calendar_id, eventId=event_id).execute()
            logging.info(f"Event with ID {event_id} has been deleted.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise

    def delete_event_by_summary(self, summary_prefix: str):
        try:
            # Use the existing method to get all events
            all_events = self.get_calendar_events()
            # Filter events based on the summary prefix
            events_to_delete = [event for event in all_events if event.summary.startswith(summary_prefix)]

            # Delete all events that match the summary prefix
            for event in events_to_delete:
                self.delete_event(event.event_id)  # Use the event_id attribute to delete the event
                logging.info(f"Event with ID {event.event_id} and summary starting '{summary_prefix}' deleted.")

            if not events_to_delete:
                logging.info(f"No event with summary starting '{summary_prefix}' found.")
        except Exception as e:
            logging.error(f"An error occurred while trying to delete the event: {e}")
            raise


# Example usage:
# google_calendar = GoogleCalendar('<your_calendar_id>', 10, datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=1))
# start_time = datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0))
# end_time = datetime.datetime.combine(datetime.date.today(), datetime.time(8, 15))
# google_calendar.create_event('test event', start_time, end_time)