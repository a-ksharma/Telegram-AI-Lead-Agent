import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os, pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """Same OAuth2 pattern as calendar — separate token file."""
    creds = None
    if os.path.exists('gmail_token.pickle'):
        with open('gmail_token.pickle', 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('gmail_token.pickle', 'wb') as f:
            pickle.dump(creds, f)
    return build('gmail', 'v1', credentials=creds)


def _build_message(to: str, subject: str, body: str) -> dict:
    message = MIMEText(body, 'html')
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}


async def send_followup_email(lead_name: str, lead_email: str, summary: str) -> dict:
    try:
        service = get_gmail_service()
        body = f"""
        <p>Hi {lead_name},</p>
        <p>Thank you for connecting with us on Telegram!</p>
        <p>{summary}</p>
        <p>We'll be in touch shortly.</p>
        <p>— The Team</p>
        """
        msg = _build_message(lead_email, "Following up from our conversation", body)
        service.users().messages().send(userId='me', body=msg).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}