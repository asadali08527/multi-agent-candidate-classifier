from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# Authenticate Gmail API
def authenticate_gmail():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    if os.path.exists('../token.pickle'):
        with open('../token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('../token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


# Fetch and filter job-related emails
def fetch_job_emails(service):
    results = service.users().messages().list(userId='me', q='subject:job OR subject:application').execute()
    messages = results.get('messages', [])
    print(f"List Of Message: {len(messages)}")

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        subject = [header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject']
        if subject:
            #print(f"Email Subject: {subject[0]}")
            # Extract the email body for processing
            snippet = msg.get('snippet', '')
            #print(f"Snippet: {snippet}")

# Run the email fetcher
if __name__ == "__main__":
    service = authenticate_gmail()
    fetch_job_emails(service)
