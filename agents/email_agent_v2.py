import os
import re

import pickle

import tempfile
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from googleapiclient.errors import HttpError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from configs.jd_template.full_stack_developer_jd import full_stack_developer_job_description
from configs.jd_template.full_stack_developer_intern_jd import full_stack_developer_intern_job_description
from configs.jd_template.ml_llm_engineer_jd import ml_llm_engineer_job_description
from configs.jd_template.ml_llm_engineer_intern_jd import ml_llm_engineer_intern_job_description
from configs.email_template.fsd import email_body as fsd_email_body
from configs.email_template.ml import email_body as ml_email_body

from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def extract_attachments(service, message):
    """Extract and process attachments from a Gmail message."""
    attachment_text = ""

    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['filename']:
                attachment_id = part['body'].get('attachmentId')
                mime_type = part['mimeType']
                if attachment_id:
                    # Download the attachment
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=message['id'], id=attachment_id
                    ).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'])

                    # Process PDF or DOCX
                    if mime_type == "application/pdf":
                        attachment_text += process_pdf(file_data)
                    elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                        attachment_text += process_docx(file_data)

    return attachment_text


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
                    # Download the attachment
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=message['id'], id=attachment_id
                    ).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'])
                    attachments.append({"filename": filename, "mime_type": mime_type, "content": file_data})

    return attachments


# Authenticate Gmail API
def authenticate_gmail():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.send']
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


# Extract the email content
def extract_email_content(message):
    body = ""
    if "data" in message.get("payload", {}).get("body", {}):
        body = base64.urlsafe_b64decode(
            message["payload"]["body"]["data"]
        ).decode("utf-8")
    elif "parts" in message.get("payload", {}):
        for part in message["payload"]["parts"]:
            if part["mimeType"] == "text/plain" and "data" in part["body"]:
                body += base64.urlsafe_b64decode(
                    part["body"]["data"]
                ).decode("utf-8")
    return body

def clean_role(role_text):
    cleaned_text = re.split(r"[\[(【]", role_text)[0]  # Remove anything after special characters
    words = cleaned_text.split()
    return " ".join(words[:3])  # Keep only the first 3 words


# Fetch job emails and evaluate candidates
def fetch_and_evaluate_candidates(service):
    results = service.users().messages().list(userId='me', q='subject:job OR subject:application OR subject:interested is:unread').execute()
    messages = results.get('messages', [])
    print(f"Total Messages Found: {len(messages)}")

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        headers = {header['name']: header['value'] for header in msg['payload']['headers']}
        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        # Ignore emails from collinear.ai domain
        if "asad@collinear.ai" in sender or "testgorilla.com" in sender or "team@hi" in sender or "usewellfound.com" in sender or "Product Manager" in subject or "Content Writer" in subject or "GTM Leader" in subject or "Sales Development" in subject:
            # print(f"Ignoring email from {sender} as it's from collinear.ai or testgorilla.com")
            continue  # Skip to the next email

        email_body = extract_email_content(msg)
        print(f"Evaluating email from {sender} with subject: {subject}")

        # Extract attachments
        attachment_data = extract_attachments_as_files(service, msg)

        # Use OpenAI to classify the candidate
        role = classify_candidate(email_body,attachment_data)
        print(f"Candidate:{sender} is applying for: {role}\n")
        role = clean_role(role)
        # Send the reply with interview process based on the role
        send_reply(service, msg, role)
        return


def truncate_text(text, max_tokens):
    if len(text) > max_tokens:
        return text[:max_tokens] + """. Based on the provided email content, determine the role the candidate is applying for. 
            Respond with only the job role like the example result given here. Example Results:  "Full Stack Developer" or "LLM Research Engineer" or "Unknown") and no additional details."""  # Truncate
    return text


# Classify candidate using OpenAI
def classify_candidate(email_body, attachments):
    jd_context = f"""
    We are hiring for the following roles:
    {full_stack_developer_job_description},
    {ml_llm_engineer_job_description},
    {full_stack_developer_intern_job_description},
    {ml_llm_engineer_intern_job_description}
    """

    prompt = f"""
    Given the following job descriptions and the email content, classify which role the candidate is applying for:

    Job Descriptions:
    {jd_context}

    Candidate Email Content:
    {email_body}
    """

    file_ids = []
    if attachments:
        prompt += "\nThe candidate has also attached the following files:\n"
        for attachment in attachments:
            filename = attachment["filename"]
            content = attachment["content"]

            # Ensure the filename has an extension
            file_extension = os.path.splitext(filename)[-1]  # Extract file extension
            if not file_extension:  # Default to '.txt' if no extension found
                file_extension = ".txt"
                filename += file_extension
            # Save as a temporary file
            with tempfile.NamedTemporaryFile(suffix=file_extension,delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name

            # Upload file to OpenAI
            with open(temp_file_path, "rb") as file:
                uploaded_file = client.files.create(file=file, purpose="assistants")
                file_ids.append(uploaded_file.id)

    # Add the final instruction to the prompt
    prompt += """
    Based on the provided email content, determine the role the candidate is applying for. 
    Respond with only the job role (e.g., "Full Stack Developer" or "LLM Research Engineer" or "Unknown") and no additional details.
    """
    try:
        if attachments:
            # Step 1: Create a thread
            thread = client.beta.threads.create(
                messages = [
                {
                    "role": "user",
                    "content": prompt,
                    "attachments": [
                        {
                            "file_id": file_id,
                            "tools": [{"type": "file_search"}]  # Required to use the attachment properly
                        }
                        for file_id in file_ids
                    ]
                }
            ])

            # Step 3: Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id="asst_Ns6W0csiyhWE0aXcg0CEt6Uv",  # Replace with your assistant ID
                instructions="Please provide responses in under 20 tokens. Respond with only the job role for example: Full Stack Developer or LLM Research Engineer or Unknown and no additional details"
            )

            # Step 4: Poll until the assistant finishes processing
            while run.status in ["queued", "in_progress"]:
                run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)

            # Step 5: Get the response
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            # Extract the assistant's response
            message_content = messages.data[0].content

            # Check if content is a list and extract the text from the first TextContentBlock
            if isinstance(message_content, list) and len(message_content) > 0:
                role = message_content[0].text.value.strip()  # Extract the plain text value
            else:
                role = "Unknown"

            return role

        else:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # or "gpt-4"
                messages=[
                    {"role": "system", "content": "Act as a technical HR recruiter"},
                    {"role": "user", "content": truncate_text(prompt, max_tokens=16000)}
                ],
                max_tokens=20,
            )
            role = response.choices[0].message.content.strip()
            return role
    except Exception as e:
        print(f"Error classifying candidate: {e}")
        return "Unknown"


def send_reply(service, message, role):
    # Get the message ID and sender's email from the message
    thread_id = message['threadId']
    headers = {header['name']: header['value'] for header in message['payload']['headers']}
    sender = headers.get("From", "")
    subject = headers.get("Subject", "")

    role_messages = {
        "Full Stack Developer": f"""
        {fsd_email_body}
        """,

        "LLM Research Engineer": f"""
        {ml_email_body}
        """
    }

    # Select the appropriate message based on the role
    role_message = role_messages.get(role, "We are reviewing your application and will get back to you shortly.")
    # Compose the reply message
    sender = extract_email(sender)
    message = create_message(to=sender,subject=subject, body=role_message)
    send_message(service, "me",message, sender )


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
    message['to'] = to  # Just the email address, not the name
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
        return send_message
    except HttpError as error:
        print(f"An error occurred while sending the email to {to}: {error}")
        raise

