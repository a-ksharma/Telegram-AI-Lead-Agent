import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os, pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Handles OAuth2 token refresh and returns a Calendar API service object."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as f:
            pickle.dump(creds, f)
    return build('calendar', 'v3', credentials=creds)


async def check_calendar_availability(days_ahead: int = 5) -> dict:
    """Return available 30-min slots in working hours for the next N days."""
    try:
        service = get_calendar_service()
        now = datetime.datetime.now(datetime.timezone.utc)
        end = now + datetime.timedelta(days=days_ahead)

        # Fetch busy periods
        body = {
            "timeMin": now.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": "primary"}]
        }
        result = service.freebusy().query(body=body).execute()
        busy_slots = result['calendars']['primary']['busy']

        # Generate candidate slots — 10am to 5pm IST, 30-min intervals
        available = []
        IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        cursor = now.astimezone(IST).replace(hour=10, minute=0, second=0, microsecond=0)
        if cursor < now.astimezone(IST):
            cursor += datetime.timedelta(days=1)

        while cursor.astimezone(datetime.timezone.utc) < end:
            slot_start = cursor.astimezone(datetime.timezone.utc)
            slot_end = slot_start + datetime.timedelta(minutes=30)
            
            # Check if slot overlaps with any busy period
            overlap = False
            for busy in busy_slots:
                b_start = datetime.datetime.fromisoformat(busy['start'])
                b_end = datetime.datetime.fromisoformat(busy['end'])
                if slot_start < b_end and slot_end > b_start:
                    overlap = True
                    break
            
            if not overlap and 10 <= cursor.hour < 17:
                available.append({
                    "display": cursor.strftime("%A, %d %B at %I:%M %p IST"),
                    "iso": cursor.isoformat()  # cursor is already in IST timezone
                })
            
            cursor += datetime.timedelta(minutes=30)
            if cursor.hour >= 17:
                cursor = (cursor + datetime.timedelta(days=1)).replace(hour=10, minute=0)

        return {"success": True, "available_slots": available[:6]}  # Return max 6 slots
    except Exception as e:
        return {"success": False, "error": str(e)}


async def book_discovery_call(lead_name: str, lead_email: str, slot_datetime: str) -> dict:
    """Create a Google Calendar event with Meet link."""
    try:
        service = get_calendar_service()
        start = datetime.datetime.fromisoformat(slot_datetime)
        end = start + datetime.timedelta(minutes=30)

        event = {
            'summary': f'Discovery Call — {lead_name}',
            'description': 'Booked via Telegram AI Lead Agent',
            'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'attendees': [{'email': lead_email}],
            'conferenceData': {
                'createRequest': {'requestId': f'meet-{lead_name}-{int(start.timestamp())}'}
            }
        }
        created = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1,
            sendUpdates='all'
        ).execute()

        meet_link = created.get('hangoutLink', '')
        event_id = created.get('id', '')
        return {"success": True, "event_id": event_id, "meet_link": meet_link, "scheduled_at": slot_datetime}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def cancel_call(calendar_event_id: str) -> dict:
    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=calendar_event_id, sendUpdates='all').execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}