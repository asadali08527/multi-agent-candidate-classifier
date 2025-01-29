from langchain.chains import SimpleSequentialChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Access the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")


# Define prompt template
prompt = PromptTemplate(
    input_variables=["skills"],
    template="Evaluate the following skills for a Machine Learning Engineer role: {skills}. Should this candidate be shortlisted?"
)

# Setup LangChain
llm = OpenAI(temperature=0.7, openai_api_key=api_key)
chain = SimpleSequentialChain(llm=llm, prompt=prompt)

# Example candidate evaluation
skills = "Python, TensorFlow, Machine Learning, SQL"
decision = chain.run(skills)
print(f"Decision: {decision}")

