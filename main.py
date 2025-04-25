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
    total_emails_sent = 0
    for message in messages:
        msg_id = message['id']
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        headers = {header['name']: header['value'] for header in msg['payload']['headers']}
        subject = headers.get("Subject", "")
        sender = extract_email(headers.get("From", ""))
        reply_to = extract_email(headers.get("Reply-To", sender))
        sender = reply_to if sender == "talent@wellfound.com" else sender
        recipients = [sender]
        
        # Ignore emails from collinear.ai domain and other specific senders
        if "noreply" in sender or "employers-noreply@indeed.com" in sender or "asad@collinear.ai" in sender or "remail.wellfound.com" in sender or "testgorilla.com" in sender or "team@hi" in sender or "usewellfound.com" in sender or "Product Manager" in subject or "Content Writer" in subject or "GTM Leader" in subject or "Sales Development" in subject :
            continue  # Skip to the next email

        print("======================================================================================")
        print(f"Candidate {sender} has applied for: {subject}")

        # Process email content
        email_body = extract_email_content(msg)
        email_address = extract_email_addresses(email_body)
        if email_address:
            recipients.append(email_address)

        # Early filtering for non-ML engineering roles
        non_ml_roles = [
            "software engineer", "software developer", "network manager", 
            "software tester", "devops engineer", "mlops engineer",
            "data engineer", "backend engineer", "frontend engineer",
            "system engineer", "full stack developer", "web developer",
            "mobile developer", "qa engineer", "test engineer",
            "database administrator", "cloud engineer", "security engineer", "senior developer", "developer"
        ]
        
        # Check if email subject indicates ML/AI role application
        ml_related_keywords = [
            "ml", "machine learning", "ai", "artificial intelligence",
            "llm", "large language model", "gen ai", "generative ai",
            "research scientist", "deep learning", "nlp"
        ]
        
        is_ml_role_application = any(keyword in subject.lower() for keyword in ml_related_keywords)
        has_non_ml_experience = any(role in email_body.lower() for role in non_ml_roles)
        
        if is_ml_role_application and has_non_ml_experience:
            print(f"Non-ML engineering candidate {sender} applied for ML role. Skipping...")
            # Mark email as read
            service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
            print(f"Marked email {msg_id} as read.")
            print("---------------------------------------------------------------------------------------")
            continue

        attachment_data = extract_attachments_as_files(service, msg)

        # Classify the role of the candidate
        role = classify_candidate(email_body, attachment_data, subject)

        # Clean and determine the role
        role = clean_role(role)
        print(f"Cleaned role: {role}")

        if (role == "Full Stack Developer" and "Full Stack Developer".lower() in subject.lower()) or (role == "LLM Research Engineer" and ("AI/ML".lower() in subject.lower() or "research" in subject.lower() or "llm" in sender.lower() or "scientist" in subject.lower() or "ml/llm" in subject.lower() or "machine learning" in subject.lower() or "large language model" in subject.lower() or "llm" in subject.lower())):

            # Send response based on the role (this should send a customized reply based on role)
            send_reply(service, msg, role, recipients)
            total_emails_sent += 1

            # Mark email as read by removing 'UNREAD' label
            service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
            print(f"Marked email {msg_id} as read.")
            print("---------------------------------------------------------------------------------------")
        else:
            print(f"Not a good match: Skipping sending email to {sender}")
            service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
            print(f"Marked email {msg_id} as read.")
            print("---------------------------------------------------------------------------------------")
    print(f"Total Emails Sent: {total_emails_sent}")

if __name__ == "__main__":
    service = authenticate_gmail()
    fetch_and_evaluate_candidates(service)
