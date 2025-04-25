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
def classify_candidate(email_body, attachments, email_subject=""):
    jd_context = f"""
    We are hiring for the following roles:
    {full_stack_developer_job_description},
    {ml_llm_engineer_job_description},
    {full_stack_developer_intern_job_description},
    {ml_llm_engineer_intern_job_description}
    """

    prompt = f"""
    Given the following job descriptions, email subject, and email content, act as a lead Technical HR to screen the candidate and determine if they are a good match for the role they applied for:

    Job Descriptions:
    {jd_context}

    Email Subject (Role Applied For):
    {email_subject}

    Candidate Email Content:
    {email_body}
    """

    file_ids = []
    if attachments:
        prompt += "\nThe candidate has also attached their CV/Resume:\n"
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
    Based on the provided email content, determine if the candidate is a good match for the role(subject) they applied for.
    Consider the following:

    PRIMARY FILTER - LOCATION:
    1. First, check the candidate's current location from email body or attachments
    2. If the candidate is NOT currently located in the United States:
       - Return "Unknown" immediately
       - Do not proceed with further evaluation
    3. Only proceed with role evaluation if the candidate is in the United States

    For LLM Research Engineer role (STRICT CRITERIA):
    1. Must have at least one of these educational qualifications:
       - Master's or PhD in AI/ML, Computer Science, Mathematics, or Statistics
    2. Must have direct experience in Large Language Models (LLMs) and at least two of these areas:
       - Generative AI
       - Machine Learning/Deep Learning
       - Natural Language Processing
       - NLP
    3. Must have hands-on experience with:
       - Training or fine-tuning LLMs
       - Working with transformer architectures
       - ML frameworks (PyTorch, TensorFlow)
    4. MUST have held one of these job titles/roles in their previous experience:
       - ML Engineer
       - Machine Learning Engineer
       - AI Engineer
       - Research Scientist (in AI/ML)
       - Gen AI Engineer
       - LLM Engineer
       - AI Research Engineer
       - Deep Learning Engineer
       - NLP Engineer
    5. DO NOT consider candidates with these job titles/roles for LLM Research Engineer position:
       - Software Engineer
       - DevOps Engineer
       - MLOps Engineer
       - Data Engineer
       - Full Stack Developer
       - Backend Engineer
       - Frontend Engineer
       - System Engineer
       - Any other non-ML engineering roles
    
    For Full Stack Developer role (FLEXIBLE CRITERIA):
    1. Should have experience in:
       - Frontend development (React, Angular, or similar)
       - Backend development (Node.js, Python, or similar)
       - Database management
    2. Bonus points for:
       - DevOps experience
       - Cloud platforms (AWS, GCP, Azure)
       - CI/CD pipelines
    
    Evaluation Process:
    1. First, check the candidate's location:
       - If not in US, return "Unknown" immediately
       - If in US, proceed with role evaluation
    2. Then, check the role mentioned in the email subject
    3. For LLM Research Engineer:
       - Strictly verify educational qualifications
       - Strictly verify required experience in AI/ML and LLMs
       - MUST verify previous job titles/roles match ML/AI positions
       - Return "Unknown" if ANY criteria are not met
    4. For Full Stack Developer:
       - More flexible evaluation
       - Consider transferable skills
       - Accept candidates with relevant experience
    
    Respond with only one of these options:
    - "Full Stack Developer" if:
       * Candidate is in US
       * Meets the flexible criteria for Full Stack Developer role
    - "LLM Research Engineer" ONLY if:
       * Candidate is in US
       * Meets ALL educational qualifications
       * Has required experience in AI/ML and LLMs
       * Has held ML/AI specific job titles/roles
       * Does NOT have only non-ML engineering experience
    - "Unknown" if:
       * Candidate is NOT in US
       * The candidate doesn't meet ANY of the strict criteria for LLM Research Engineer
       * The candidate has only non-ML engineering experience
       * The candidate doesn't have relevant experience for Full Stack Developer
       * The role cannot be determined
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
