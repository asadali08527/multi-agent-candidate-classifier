import base64
import os
import pickle
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from googleapiclient.errors import HttpError

from configs.email_template.fsd import email_body as fsd_email_body
from configs.email_template.ml import email_body as ml_email_body

# Load environment variables
load_dotenv()

def authenticate_gmail():
    """Authenticate and return Gmail service."""
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']
    creds = None
    if os.path.exists('../token.pickle'):
        with open('../token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('./credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('../token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def extract_attachments_as_files(service, message):
    """Extract attachments and return their raw content."""
    attachments = []
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['filename']:
                attachment_id = part['body'].get('attachmentId')
                mime_type = part['mimeType']
                filename = part['filename']
                if attachment_id:
                    attachment = service.users().messages().attachments().get(userId='me', messageId=message['id'], id=attachment_id).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'])
                    attachments.append({"filename": filename, "mime_type": mime_type, "content": file_data})
    return attachments

def send_reply(service, message, role, recipients):
    # Get the message ID and sender's email from the message
    thread_id = message['threadId']
    headers = {header['name']: header['value'] for header in message['payload']['headers']}
    subject = f"Next Steps for {role} Position"
    
    # Define custom messages for different roles
    role_messages = {
        "Full Stack Developer": f"""
        {fsd_email_body}
        """,

        "LLM Research Engineer": f"""
        {ml_email_body}
        """
    }

    # Select the appropriate message based on the role
    role_message = role_messages.get(role, "We are reviewing your application and will get back to you shortly.\nRegards,\n-Asad")
    # Compose the reply message
    message = create_message(to=recipients, subject=subject, body=role_message)
    send_message(service, "me", message, recipients)


# Function to extract email address from the sender field
def extract_email(sender):
    # This will match the email part and ignore the name
    match = re.search(r'<(.+)>', sender)
    if match:
        return match.group(1)
    else:
        return sender  # If no name is present, return the sender as is


def create_message(to, subject, body):
    """Create a message for an email."""
    message = MIMEMultipart()
    # If multiple recipients, join them with a comma
    if isinstance(to, list):
        message['to'] = ', '.join(to)
    else:
        message['to'] = to
    message['subject'] = subject
    message['From'] = f"Asad <asad@collinear.ai>"
    msg = MIMEText(body, 'html')
    message.attach(msg)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}


def send_message(service, sender, message, to):
    """Send an email message."""
    try:
        message_response = service.users().messages().send(userId=sender, body=message).execute()
        print(f"Message Sent to:{to}, Message Id: {message_response['id']}")
    except HttpError as error:
        print(f"An error occurred while sending the email to {to}: {error}")
        raise
