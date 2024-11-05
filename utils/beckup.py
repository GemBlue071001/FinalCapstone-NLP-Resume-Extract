# mistral.py

import os
import json
import logging
from huggingface_hub import InferenceClient
from huggingface_hub.utils._errors import BadRequestError
from dotenv import load_dotenv
from utils.fileTotext import extract_text_based_on_format
import re
from utils.spacy import Parser_from_model

# Load environment variables from .env file
load_dotenv()

# Authenticate with Hugging Face
HFT = os.getenv('HF_TOKEN') 
if not HFT:
    raise ValueError("Hugging Face token is not set in environment variables.")
client = InferenceClient(model="mistralai/Mistral-Nemo-Instruct-2407", token=HFT)

# Function to clean model output
def Data_Cleaner(text):
    pattern = r".*?format:"
    result = re.split(pattern, text, maxsplit=1)
    if len(result) > 1:
        text_after_format = result[1].strip().strip('`').strip('json')
    else:
        text_after_format = text.strip().strip('`').strip('json')
        
    return text_after_format

# Function to call Mistral and process output
def Model_ProfessionalDetails_Output(resume, client):
    system_role = {
    "role": "system",
    "content": "You are a skilled resume parser. Your task is to extract professional details from resumes in a structured JSON format defined by the User. Ensure accuracy and completeness while maintaining the format provided and if field are missing just return 'not found'."
    }
    user_prompt = {
    "role": "user",
    "content": f'''Act as a resume parser for the following text given in text: {resume}
    Extract the text in the following output JSON string as:
    {{
        "professional": {{
             "skills": "Extract and list all technical skills, non-technical skills, programming languages, frameworks, domains, and technologies based on the resume.",
             "soft_skills": "Extract non-technical skills, Communication skills, and soft skills based on the resume."
             "projects": "Include only the project names, titles, or headers mentioned in the resume. ",
             "projects_experience": ["Include overall project Experiences and about project in short mentioned in the resume.] ",
             "experience": "Include the total experience in months or years as mentioned in the resume.",
             "companies_worked_at": "Include the names of all companies worked at according to the resume. ",
             "certification": "Include any certifications obtained based on the resume. ",
             "worked_as": "Include the names of roles worked as according to the resume.", 
             "qualification":"Extract and list the qualifications based on the resume, (qualifications likes B.Tech). If none are found, return 'No education listed'.",
             "course": "Extract the name of the Learning Course completed based on the resume. If not found, return 'No Course listed'.",
             "university": "Extract the name of the university or Collage or Intitute attended based on the resume. If not found, return 'No university listed'.",
             "year_of_graduation": "Extract the year of graduation from the resume. If not found, return 'No year of graduation listed'."                       
        }}
    }}
    Json Output:
    ''' 
    }


    response = ""
    for message in client.chat_completion(messages=[system_role, user_prompt], max_tokens=3000, stream=True, temperature=0.35):
        response += message.choices[0].delta.content
    
    try:
        clean_response = Data_Cleaner(response)
        parsed_response = json.loads(clean_response)
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
        return {}
    
    return parsed_response

def Model_PersonalDetails_Output(resume, client):
    system_role = {
    "role": "system",
    "content": "You are a skilled resume parser. Your task is to extract professional details from resumes in a structured JSON format defined by the User. Ensure accuracy and completeness while maintaining the format provided and if field are missing just return 'not found'."
    }
    user_prompt = {
    "role": "user",
    "content": f'''Act as a resume parser for the following text given in text: {resume}
    Extract the text in the following output JSON string as:
    {{
        "personal": {{
            "name": "Extract the full name based on the resume. If not found, return 'No name listed'.",
            "contact_number": "Extract the contact number from the resume. If not found, return 'No contact number listed'.",
            "email": "Extract the email address from the resume. If not found, return 'No email listed'.",
            "Address": "Extract the Address or address from the resume. If not found, return 'No Address listed'.",
            "link": "Extract any relevant links (e.g., portfolio, LinkedIn) from the resume. If not found, return 'No link listed'."
        }}
    }} 
    output:
    '''
    }

    # Response
    response = ""
    for message in client.chat_completion(
        messages=[system_role, user_prompt],
        max_tokens=3000,
        stream=True,
        temperature=0.35,
    ):
        response += message.choices[0].delta.content

    # Handle cases where the response might have formatting issues
    try:
        #print('The Og response:-->',response)
        clean_response=Data_Cleaner(response)
        #print("After data cleaning",clean_response)
        parsed_response = json.loads(clean_response)
        
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        print("Raw Response:", response)        
        return {}

    return parsed_response


# # Fallback to SpaCy if Mistral fails

def process_resume_data(file_path):
    resume_text, hyperlinks = extract_text_based_on_format(file_path)
    print("Resume converted to text successfully.")
    
    if not resume_text:
        return {"error": "Text extraction failed"}
    
    # Attempt to use Mistral model for parsing
    try:
        # Extract personal details using Mistral
        per_data = Model_PersonalDetails_Output(resume_text, client)
        
        # Extract professional details using Mistral
        pro_data = Model_ProfessionalDetails_Output(resume_text, client)
        
        
        
        # Check if per_data and pro_data have been populated correctly
        if not per_data:
            logging.warning("Mistral personal data extraction failed.")
            per_data = {}
        
        if not pro_data:
            logging.warning("Mistral professional data extraction failed.")
            pro_data = {}
        
        # Combine both personal and professional details into a structured output
        result = {
            "personal": {
                "name":  per_data.get('personal', {}).get('name', 'Not found'),
                "contact": per_data.get('personal', {}).get('contact_number', 'Not found'),
                "email": per_data.get('personal', {}).get('email', 'Not found'),
                "location": per_data.get('personal', {}).get('Address', 'Not found'),
                "link": hyperlinks
            },
            "professional": {
                "skills": pro_data.get('professional', {}).get('skills', 'Not found'),
                "soft_skills": pro_data.get('professional', {}).get('soft_skills', 'Not found'),
                "experience": [
                    {
                        "company": pro_data.get('professional', {}).get('companies_worked_at', 'Not found'),
                        "projects": pro_data.get('professional', {}).get('projects', 'Not found'),
                        "role": pro_data.get('professional', {}).get('worked_as', 'Not found'),
                        "years": pro_data.get('professional', {}).get('experience', 'Not found'),
                        "project_experience": pro_data.get('professional', {}).get('projects_experience', 'Not found')
                    }
                ],
                "education": [
                    {
                        "qualification": pro_data.get('professional', {}).get('qualification', 'Not found'),
                        "university": pro_data.get('professional', {}).get('university', 'Not found'),
                        "course": pro_data.get('professional', {}).get('course', 'Not found'),
                        "certificate": pro_data.get('professional', {}).get('certification', 'Not found')
                    }
                ]
            }
        }
        
        # If Mistral produces valid output, return it
        if per_data or pro_data:
            print("------Mistral-----")
            return result
        else:
            raise ValueError("Mistral returned no output")
    
    # Handle HuggingFace API or Mistral model errors
    except BadRequestError as e:
        logging.error(f"HuggingFace API error: {e}. Falling back to SpaCy.")
        print(f"HuggingFace API error: {e}. Falling back to SpaCy.")
    except Exception as e:
        logging.error(f"An error occurred while processing with Mistral: {e}. Falling back to SpaCy.")
        print(f"An error occurred while processing with Mistral: {e}. Falling back to SpaCy.")
    
    # Fallback to SpaCy if Mistral fails
    logging.warning("Mistral failed, switching to SpaCy.")
    print("------Spacy-----")
    return Parser_from_model(file_path)


# /////////////////////////////////////////////
# ////////////////Spacy.py/////////////////////
# /////////////////////////////////////////////


import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from pathlib import Path
from spacy.tokens import DocBin
import random

# Load the training data from the .spacy file
def load_data_from_spacy_file(file_path):
    # Initialize a blank English model to ensure compatibility
    nlp = spacy.blank("en")
    
    # Load the DocBin object and get documents
    try:
        doc_bin = DocBin().from_disk(file_path)
        docs = list(doc_bin.get_docs(nlp.vocab))
        return docs
    except Exception as e:
        print(f"Error loading data from .spacy file: {e}")
        return []


# Train model function
def train_model(epochs, model_path):
    # Initialize a blank English model
    nlp = spacy.blank("en")
    
    # Create an NER component and add it to the pipeline
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
        
    nlp.add_pipe("sentencizer")

    # Define all possible entity labels
    labels = [
        "PERSON", "CONTACT", "EMAIL", "ABOUT", "EXPERIENCE", "YEARS_EXPERIENCE",
        "UNIVERSITY", "SOFT_SKILL", "INSTITUTE", "LAST_QUALIFICATION_YEAR", "JOB_TITLE",
        "COMPANY", "COURSE", "DOB", "HOBBIES", "LINK", "SCHOOL", "QUALIFICATION",
        "LANGUAGE", "LOCATION", "PROJECTS", "SKILL", "CERTIFICATE"
    ]

    # Add labels to the NER component
    for label in labels:
        ner.add_label(label)

    # Load the training data
    train_data = load_data_from_spacy_file("./data/Spacy_data.spacy")

    # Start the training
    optimizer = nlp.begin_training()

    epoch_losses = []
    best_loss = float('inf')

    # Training loop
    for epoch in range(epochs):
        losses = {}
        random.shuffle(train_data)  # Shuffle data for better training
        
        # Create minibatches
        batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))
        
        for batch in batches:
            texts, annotations = zip(*[(doc.text, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}) for doc in batch])
            
            # Convert to Example objects
            examples = [Example.from_dict(nlp.make_doc(text), annotation) for text, annotation in zip(texts, annotations)]
               
            # Update the model
            nlp.update(examples, sgd=optimizer, drop=0.35, losses=losses)
        
        current_loss = losses.get("ner", float('inf'))
        epoch_losses.append(current_loss)
        
        print(f"Losses at epoch {epoch + 1}: {losses}")
        
        # Stop training if the loss is zero
        if current_loss == 0:
            break
        
        # Save the best model
        if current_loss < best_loss:
            best_loss = current_loss
            nlp.to_disk(model_path)
    
    # Save the final model
    nlp.to_disk(model_path)

    return epoch_losses
