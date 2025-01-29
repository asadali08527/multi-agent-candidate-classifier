import re

def clean_role(role_text):
    """Clean and return the role from the text."""
    cleaned_text = re.split(r"[\[(【]", role_text)[0]  # Remove anything after special characters
    words = cleaned_text.replace("\"","").replace('\'',"").split()
    return " ".join(words[:3])  # Keep only the first 3 words


def truncate_text(text, max_tokens):
    if len(text) > max_tokens:
        return text[:max_tokens] + """. Based on the provided email content, determine the role the candidate is applying for. 
            Respond with only the job role like the example result given here. Example Results:  "Full Stack Developer" or "LLM Research Engineer" or "Unknown") and no additional details."""  # Truncate
    return text
