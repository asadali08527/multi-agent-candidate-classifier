from services.gmail_service import send_reply, extract_email
from services.gmail_service import authenticate_gmail, extract_attachments_as_files
from services.openai_service import classify_candidate
from utils.file_utils import extract_email_content, extract_email_addresses
from utils.text_utils import clean_role


def fetch_and_evaluate_candidates(service):
    """Fetch job emails, classify candidates, and send email replies."""
    results = service.users().messages().list(userId='me',
                                              q='subject:job OR subject:application OR subject:interested is:unread').execute()
    messages = results.get('messages', [])
    print(f"Total Messages Found: {len(messages)}")
    not_a_good_match = 0
    for message in messages:
        msg_id = message['id']
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        headers = {header['name']: header['value'] for header in msg['payload']['headers']}
        subject = headers.get("Subject", "")
        sender = extract_email(headers.get("From", ""))
        reply_to = extract_email(headers.get("Reply-To", sender))
        sender = reply_to if sender == "talent@wellfound.com" else sender
        recipients = [sender]
        # Ignore emails from collinear.ai domain
        if "noreply" in sender or "employers-noreply@indeed.com" in sender or "asad@collinear.ai" in sender or "remail.wellfound.com" in sender or "testgorilla.com" in sender or "team@hi" in sender or "usewellfound.com" in sender or "Product Manager" in subject or "Content Writer" in subject or "GTM Leader" in subject or "Sales Development" in subject :
            # print(f"Ignoring email from {sender} as it's from collinear.ai or testgorilla.com")
            continue  # Skip to the next email
        print("======================================================================================")
        print(f"Candidate {sender} has applied for: {subject}")

        # Process email content
        email_body = extract_email_content(msg)
        email_address = extract_email_addresses(email_body)
        if email_address:
            recipients.append(email_address)
        attachment_data = extract_attachments_as_files(service, msg)

        # Classify the role of the candidate
        role = classify_candidate(email_body, attachment_data)

        # Clean and determine the role
        role = clean_role(role)
        print(f"Cleaned role: {role}")

        if (role == "Full Stack Developer" and "Full Stack Developer".lower() in subject.lower()) or (role == "LLM Research Engineer" and ("AI/ML".lower() in subject.lower() or "research" in subject.lower() or "llm" in sender.lower() or "scientist" in subject.lower() or "ml/llm" in subject.lower() or "machine learning" in subject.lower() or "large language model" in subject.lower())):

            # Send response based on the role (this should send a customized reply based on role)
            send_reply(service, msg, role, recipients)

            # Mark email as read by removing 'UNREAD' label
            service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
            print(f"Marked email {msg_id} as read.")
            print("---------------------------------------------------------------------------------------")
        else:
            not_a_good_match+=1
            print(f"Not a good match: Skipping sending email to {sender}")
            print("---------------------------------------------------------------------------------------")
    print(f"Total Sent Email: {100-not_a_good_match}")

if __name__ == "__main__":
    service = authenticate_gmail()
    fetch_and_evaluate_candidates(service)
