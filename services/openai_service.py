from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile

from utils.text_utils import truncate_text
from configs.jd_template.full_stack_developer_intern_jd import full_stack_developer_intern_job_description
from configs.jd_template.full_stack_developer_jd import full_stack_developer_job_description
from configs.jd_template.ml_llm_engineer_intern_jd import ml_llm_engineer_intern_job_description
from configs.jd_template.ml_llm_engineer_jd import ml_llm_engineer_job_description

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

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
    Given the following job descriptions and the email content, We want you to act as lead Technical HR to screen the candidate and classify which role the candidate is eligible for:

    Job Descriptions:
    {jd_context}

    Candidate Email Content:
    {email_body}
    """

    file_ids = []
    if attachments:
        prompt += "\nThe candidate has also attached the his CV/Resume:\n"
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
    Based on the provided email content, determine the role the candidate is eligible for. 
    Respond with only the job role (e.g., "Full Stack Developer" or "LLM Research Engineer" or "Unknown") and if the candidate is not eligible for either "Full Stack Developer" or "LLM Research Engineer" return Unknown in the response.
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
