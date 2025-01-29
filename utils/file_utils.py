import base64
import re

from bs4 import BeautifulSoup


def extract_email_content(message):
    """Extract the email content (body) from a message and remove HTML tags."""
    body = ""

    if "data" in message.get("payload", {}).get("body", {}):
        # Decode the email body
        body = base64.urlsafe_b64decode(message["payload"]["body"]["data"]).decode("utf-8")
        body = extract_text_from_html(body)

    elif "parts" in message.get("payload", {}):
        for part in message["payload"]["parts"]:
            mime_type = part.get("mimeType", "")
            # print("MIME: "+mime_type)
            if mime_type == "text/plain" and "data" in part["body"]:
                body += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            elif mime_type == "text/html" and "data" in part["body"]:
                html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                body += extract_text_from_html(html_body)

    return body.strip()

def extract_text_from_html(html_content):
    """Extract and clean text from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def extract_email_addresses(text):
    """Extract all email addresses from the given text."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else ""  # Return first email or empty string
