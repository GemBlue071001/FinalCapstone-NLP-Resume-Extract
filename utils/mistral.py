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

# # Authenticate with Hugging Face
# HFT = os.getenv('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')

# if not HFT:
#     raise ValueError("Hugging Face token is not set in environment variables.")
# client = InferenceClient(model="mistralai/Mistral-Nemo-Instruct-2407", token=HFT)

HFT = os.getenv('HUGGINGFACE_TOKEN')

if not HFT:
    # Check if token is passed directly
    HFT = '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'
    if not HFT:
        raise ValueError("Hugging Face token is not set in environment variables or directly.")

try:
    # Initialize the client with error handling
    client = InferenceClient(
        model="mistralai/Mistral-Nemo-Instruct-2407",
        token=HFT
    )
except Exception as e:
    raise ValueError(f"Failed to initialize Hugging Face client: {str(e)}")

# Function to clean model output
'''
def Data_Cleaner(text):
    pattern = r".*?format:"
    result = re.split(pattern, text, maxsplit=1)
    if len(result) > 1:
        # Handle edge cases where JSON might not be properly formatted after 'format:'
        text_after_format = result[1].strip().strip('`').strip('json')
    else:
        text_after_format = text.strip().strip('`').strip('json')

    # Try to ensure valid JSON is returned
    try:
        json.loads(text_after_format)  # Check if it's valid JSON
        return text_after_format
    except json.JSONDecodeError:
        logging.error("Data cleaning led to invalid JSON")
        return text  # Return the original text if cleaning goes wrong
'''
def Data_Cleaner(text):
    """
    Preprocess the JSON string to remove extra spaces, tabs, and newlines.
    """   
    # Use a regex pattern to extract JSON if it exists within ```json and ```
    pattern = r"```json\s*(\{.*?\})\s*```"  # Non-greedy matching inside braces
    match = re.search(pattern, text, re.DOTALL)  # DOTALL to match newlines

    if match:
        json_str = match.group(1).strip()  # Extract JSON block
    else:
        # If no match, check if text itself is a JSON object
        try:
            json_obj = json.loads(text.strip())  # Attempt to load the text as JSON
             # Remove leading and trailing whitespace
            text = text.strip()
            # Remove unnecessary newlines and tabs
            text = re.sub(r'\s*\n\s*', ' ', text)  # Replace newlines with a space
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
            text = re.sub(r'\s*([{}:,])\s*', r'\1', text)  # Remove spaces around braces, colons, and commas
            return text  # Return the parsed JSON as a dictionary
        except json.JSONDecodeError:
            logging.error("No valid JSON found in the text")
            return text  # Return the original text if no valid JSON is found

    # Validate and return the cleaned JSON if it's valid
    try:
        json_obj = json.loads(json_str)  # Validate JSON
        return json_str  # Return the parsed JSON as a dictionary
    except json.JSONDecodeError:
        logging.error("Extracted text is not valid JSON")
        return text  # Return the original text if JSON decoding fa

# Function to call Mistral and process output
def Model_ProfessionalDetails_Output(resume, client):
    system_role = {
    "role": "system",
    "content": "You are a skilled resume parser. Your task is to extract Professional details from resumes in a structured JSON format defined by the User. Ensure accuracy and completeness while maintaining the format provided and if field are missing just return []."
    }
    user_prompt = {
    "role": "user",
    "content": f'''<s>[INST] Act as a resume parser for the following text given in text: {resume}
    Extract the text in the following output JSON string as:
    {{
        "professional": {{
            "technical_skills": ["List all technical skills, programming languages, frameworks, and technologies mentioned in the resume, ensuring they are not mixed with other skill types. If not found, return []"],
            "non_technical_skills": ["List all non-technical skills such as leadership, teamwork, and communication skills, ensuring they are not mixed with technical skills. If not found, return []"],
            "tools": ["List and extract all software tools, platforms, and applications referenced in the resume, distinctly separate from skills. If not found, return []"],
            "companies_worked_at": ["List and Extract all companies or industries where the person has worked, as mentioned in the resume. If not found, return []"],
            "projects": ["Extract all projects names or titles mentioned in the resume. If not found, return []"],
            "projects_experience": ["Summarize overall project experiences in a list, providing a brief description of each project as detailed in the resume. If not found, return []"],
            "experience": ["Calculate and give the total work experience in years, even if overlapping as mentioned in the resume. If not found, return []"],           
            "roles": ["List and Extract all job titles or roles of the person, as mentioned in the resume. If not found, return []"]           
        }}
    }}
    output:
    [/INST]</s>
    ''' 
    }

    #response = ""
    #for message in client.chat_completion(messages=[system_role, user_prompt], max_tokens=4096, stream=True):#, temperature=0.35):
    #    response += message.choices[0].delta.content
        
    data = client.chat_completion(messages=[system_role, user_prompt], max_tokens=3000, stream=False, temperature=0.35)   
    response = data.choices[0].message.content
    
    try:
        clean_response = Data_Cleaner(response)
        print("This is clean_response data----> ",clean_response)
        parsed_response = json.loads(clean_response)
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
        return {}
    
    return parsed_response

# Function to call Mistral and process output
def Model_EducationalDetails_Output(resume, client):
    system_role = {
    "role": "system",
    "content": "You are a skilled resume parser. Your task is to Extract All Educational qualifications, including Degrees and Certifications  from resumes in a structured JSON format defined by the User. Ensure accuracy and completeness while maintaining the format provided and if field are missing just return []."
    }
    user_prompt = {
    "role": "user",
    "content": f'''<s>[INST] Act as a resume parser for the following text given in text: {resume}
    Extract the text in the following output JSON string as:
    {{
        "educational": {{                        
            "certifications": ["List and extract all certifications mentioned in the resume. If none are found, return []."],         
            "qualifications": ["List and extract all educational qualifications, including degrees (e.g., BBA, MBA), their full forms, and associated levels (e.g., undergraduate, postgraduate) from the resume. If [] are found, return []."],
            "university": ["List and extract the name of the university, college, or institute attended based on the resume. If not found, return []."],
            "courses": ["List and extract the names of completed courses or based on the resume. If none are found, return []."]
        }}
    }}
    output:
    [/INST]</s>
    ''' 
    }

    #response = ""
    #for message in client.chat_completion(messages=[system_role, user_prompt], max_tokens=4096, stream=True):#, temperature=0.35):
    #    response += message.choices[0].delta.content
    data = client.chat_completion(messages=[system_role, user_prompt], max_tokens=3000, stream=False, temperature=0.35)    
    response = data.choices[0].message.content
    
    try:
        clean_response = Data_Cleaner(response)
        print("This is clean_response data----> ",clean_response)
        parsed_response = json.loads(clean_response)
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e}")
        return {}
    
    return parsed_response

def Model_PersonalDetails_Output(resume, client):
    system_role = {
    "role": "system",
    "content": "You are a skilled resume parser. Your task is to extract personal details from resumes in a structured JSON format defined by the User. Ensure accuracy and completeness while maintaining the format provided and if field are missing just return []."
    }
    user_prompt = {
    "role": "user",
    "content": f'''<s>[INST] Act as a resume parser for the following text given in text: {resume}
    Extract the text in the following output JSON string as:
    {{
        "personal": {{
            "name": ["Extract the full name based on the resume. If not found, return []."],
            "contact_number": ["Extract the contact number from the resume. If not found, return []."],
            "email": ["Extract the email address from the resume. If not found, return []."],
            "address": ["Extract the address or address as mentioned in the resume. If not found, return []."],
            "link": ["Extract any relevant links (e.g., portfolio, LinkedIn) from the resume. If not found, return [].]"            
        }}
    }} 
    output:
    [/INST]</s>
    '''
    }

    # Response
    #response = ""
    #for message in client.chat_completion(messages=[system_role, user_prompt], max_tokens=3000, stream=True):#, temperature=0.35):
    #response += message.choices[0].delta.content

    data = client.chat_completion(messages=[system_role, user_prompt], max_tokens=3000, stream=False, temperature=0.35)    
    response = data.choices[0].message.content
    
    # Handle cases where the response might have formatting issues
    try:
        #print('The Og response:-->',response)
        clean_response=Data_Cleaner(response)
        print("This is clean_response data----> ",clean_response)
        parsed_response = json.loads(clean_response)
        
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        print("Raw Response:", response)        
        return {}

    return parsed_response

# # Fallback to SpaCy if Mistral fails

# Add regex pattern for LinkedIn and GitHub links
linkedin_pattern = r"https?://(?:www\.)?linkedin\.com/[\w\-_/]+"
github_pattern = r"https?://(?:www\.)?github\.com/[\w\-_/]+"
email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
contact_pattern = r"^\+?[\d\s\-()]{7,15}$"

def extract_links(hyperlinks):
    linkedin_links = []
    github_links = []
    
    # Iterate through the hyperlinks and apply regex to find LinkedIn and GitHub links
    for link in hyperlinks:
        if re.match(linkedin_pattern, link):
            linkedin_links.append(link)
        elif re.match(github_pattern, link):
            github_links.append(link)
    
    return linkedin_links, github_links

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def is_valid_contact(contact):
        patterns = [
        r'^\+91[\s\.\-\/]?\(?0?\)?[\s\-\.\/]?\d{5}[\s\-\.\/]?\d{5}$',  # +91 with optional 0 and separators
        r'^\+91[\s\.\-\/]?\d{5}[\s\-\.\/]?\d{5}$',  # +91 with 10 digits separated
        r'^\d{5}[\s\-\.\/]?\d{5}$',  # Local format without country code
        r'^\+91[\s\.\-\/]?\d{10}$',  # +91 with 10 digits together
        r'^\d{10}$',  # 10 digits together
        r'^\+91[\s\.\-\/]?\(?\d{5}\)?[\s\-\.\/]?\d{5}[\s\-\.\/]?\d{5}$'  # +91 with varying separators
        r'\+1\s\(\d{3}\)\s\d{3}-\d{4} ',               # USA/Canada Intl +1 (XXX) XXX-XXXX
        r'\(\d{3}\)\s\d{3}-\d{4} ',                    # USA/Canada STD (XXX) XXX-XXXX
        r'\(\d{3}\)\s\d{3}\s\d{4} ',                   # USA/Canada (XXX) XXX XXXX
        r'\(\d{3}\)\s\d{3}\s\d{3} ',                   # USA/Canada (XXX) XXX XXX
        r'\+1\d{10} ',                                 # +1 XXXXXXXXXX
        r'\d{10} ',                                    # XXXXXXXXXX
        r'\+44\s\d{4}\s\d{6} ',                        # UK Intl +44 XXXX XXXXXX
        r'\+44\s\d{3}\s\d{3}\s\d{4} ',                 # UK Intl +44 XXX XXX XXXX
        r'0\d{4}\s\d{6} ',                             # UK STD 0XXXX XXXXXX
        r'0\d{3}\s\d{3}\s\d{4} ',                      # UK STD 0XXX XXX XXXX
        r'\+44\d{10} ',                                # +44 XXXXXXXXXX
        r'0\d{10} ',                                   # 0XXXXXXXXXX
        r'\+61\s\d\s\d{4}\s\d{4} ',                    # Australia Intl +61 X XXXX XXXX
        r'0\d\s\d{4}\s\d{4} ',                         # Australia STD 0X XXXX XXXX
        r'\+61\d{9} ',                                 # +61 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+91\s\d{5}-\d{5} ',                         # India Intl +91 XXXXX-XXXXX
        r'\+91\s\d{4}-\d{6} ',                         # India Intl +91 XXXX-XXXXXX
        r'\+91\s\d{10} ',                              # India Intl +91 XXXXXXXXXX
        r'0\d{2}-\d{7} ',                              # India STD 0XX-XXXXXXX
        r'\+91\d{10} ',                                # +91 XXXXXXXXXX
        r'\+49\s\d{4}\s\d{8} ',                        # Germany Intl +49 XXXX XXXXXXXX
        r'\+49\s\d{3}\s\d{7} ',                        # Germany Intl +49 XXX XXXXXXX
        r'0\d{3}\s\d{8} ',                             # Germany STD 0XXX XXXXXXXX
        r'\+49\d{12} ',                                # +49 XXXXXXXXXXXX
        r'\+49\d{10} ',                                # +49 XXXXXXXXXX
        r'0\d{11} ',                                   # 0XXXXXXXXXXX
        r'\+86\s\d{3}\s\d{4}\s\d{4} ',                 # China Intl +86 XXX XXXX XXXX
        r'0\d{3}\s\d{4}\s\d{4} ',                      # China STD 0XXX XXXX XXXX
        r'\+86\d{11} ',                                # +86 XXXXXXXXXXX
        r'\+81\s\d\s\d{4}\s\d{4} ',                    # Japan Intl +81 X XXXX XXXX
        r'\+81\s\d{2}\s\d{4}\s\d{4} ',                 # Japan Intl +81 XX XXXX XXXX
        r'0\d\s\d{4}\s\d{4} ',                         # Japan STD 0X XXXX XXXX
        r'\+81\d{10} ',                                # +81 XXXXXXXXXX
        r'\+81\d{9} ',                                 # +81 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+55\s\d{2}\s\d{5}-\d{4} ',                  # Brazil Intl +55 XX XXXXX-XXXX
        r'\+55\s\d{2}\s\d{4}-\d{4} ',                  # Brazil Intl +55 XX XXXX-XXXX
        r'0\d{2}\s\d{4}\s\d{4} ',                      # Brazil STD 0XX XXXX XXXX
        r'\+55\d{11} ',                                # +55 XXXXXXXXXXX
        r'\+55\d{10} ',                                # +55 XXXXXXXXXX
        r'0\d{10} ',                                   # 0XXXXXXXXXX
        r'\+33\s\d\s\d{2}\s\d{2}\s\d{2}\s\d{2} ',      # France Intl +33 X XX XX XX XX
        r'0\d\s\d{2}\s\d{2}\s\d{2}\s\d{2} ',           # France STD 0X XX XX XX XX
        r'\+33\d{9} ',                                 # +33 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+7\s\d{3}\s\d{3}-\d{2}-\d{2} ',             # Russia Intl +7 XXX XXX-XX-XX
        r'8\s\d{3}\s\d{3}-\d{2}-\d{2} ',               # Russia STD 8 XXX XXX-XX-XX
        r'\+7\d{10} ',                                 # +7 XXXXXXXXXX
        r'8\d{10} ',                                   # 8 XXXXXXXXXX
        r'\+27\s\d{2}\s\d{3}\s\d{4} ',                 # South Africa Intl +27 XX XXX XXXX
        r'0\d{2}\s\d{3}\s\d{4} ',                      # South Africa STD 0XX XXX XXXX
        r'\+27\d{9} ',                                 # +27 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+52\s\d{3}\s\d{3}\s\d{4} ',                 # Mexico Intl +52 XXX XXX XXXX
        r'\+52\s\d{2}\s\d{4}\s\d{4} ',                 # Mexico Intl +52 XX XXXX XXXX
        r'01\s\d{3}\s\d{4} ',                          # Mexico STD 01 XXX XXXX
        r'\+52\d{10} ',                                # +52 XXXXXXXXXX
        r'01\d{7} ',                                   # 01 XXXXXXX
        r'\+234\s\d{3}\s\d{3}\s\d{4} ',                # Nigeria Intl +234 XXX XXX XXXX
        r'0\d{3}\s\d{3}\s\d{4} ',                      # Nigeria STD 0XXX XXX XXXX
        r'\+234\d{10} ',                               # +234 XXXXXXXXXX
        r'0\d{10} ',                                   # 0XXXXXXXXXX
        r'\+971\s\d\s\d{3}\s\d{4} ',                   # UAE Intl +971 X XXX XXXX
        r'0\d\s\d{3}\s\d{4} ',                         # UAE STD 0X XXX XXXX
        r'\+971\d{8} ',                                # +971 XXXXXXXX
        r'0\d{8} ',                                    # 0XXXXXXXX
        r'\+54\s9\s\d{3}\s\d{3}\s\d{4} ',              # Argentina Intl +54 9 XXX XXX XXXX
        r'\+54\s\d{1}\s\d{4}\s\d{4} ',                 # Argentina Intl +54 X XXXX XXXX
        r'0\d{3}\s\d{4} ',                             # Argentina STD 0XXX XXXX
        r'\+54\d{10} ',                                # +54 9 XXXXXXXXXX
        r'\+54\d{9} ',                                 # +54 XXXXXXXXX
        r'0\d{7} ',                                    # 0XXXXXXX
        r'\+966\s\d\s\d{3}\s\d{4} ',                   # Saudi Intl +966 X XXX XXXX
        r'0\d\s\d{3}\s\d{4} ',                         # Saudi STD 0X XXX XXXX
        r'\+966\d{8} ',                                # +966 XXXXXXXX
        r'0\d{8} ',                                    # 0XXXXXXXX
        r'\+1\d{10} ',                                 # +1 XXXXXXXXXX
        r'\+1\s\d{3}\s\d{3}\s\d{4} ',                  # +1 XXX XXX XXXX
        r'\d{5}\s\d{5} ',                              # XXXXX XXXXX                              
        r'\d{10} ',                                    # XXXXXXXXXX
        r'\+44\d{10} ',                                # +44 XXXXXXXXXX
        r'0\d{10} ',                                   # 0XXXXXXXXXX
        r'\+61\d{9} ',                                 # +61 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+91\d{10} ',                                # +91 XXXXXXXXXX
        r'\+49\d{12} ',                                # +49 XXXXXXXXXXXX
        r'\+49\d{10} ',                                # +49 XXXXXXXXXX
        r'0\d{11} ',                                   # 0XXXXXXXXXXX
        r'\+86\d{11} ',                                # +86 XXXXXXXXXXX
        r'\+81\d{10} ',                                # +81 XXXXXXXXXX
        r'\+81\d{9} ',                                 # +81 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+55\d{11} ',                                # +55 XXXXXXXXXXX
        r'\+55\d{10} ',                                # +55 XXXXXXXXXX
        r'0\d{10} ',                                   # 0XXXXXXXXXX
        r'\+33\d{9} ',                                 # +33 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX
        r'\+7\d{10} ',                                 # +7 XXXXXXXXXX
        r'8\d{10} ',                                   # 8 XXXXXXXXXX
        r'\+27\d{9} ',                                 # +27 XXXXXXXXX
        r'0\d{9} ',                                    # 0XXXXXXXXX (South Africa STD)
        r'\+52\d{10} ',                                # +52 XXXXXXXXXX
        r'01\d{7} ',                                   # 01 XXXXXXX
        r'\+234\d{10} ',                               # +234 XXXXXXXXXX
        r'0\d{10} ',                                   # 0XXXXXXXXXX
        r'\+971\d{8} ',                                # +971 XXXXXXXX
        r'0\d{8} ',                                    # 0XXXXXXXX
        r'\+54\s9\s\d{10} ',                           # +54 9 XXXXXXXXXX
        r'\+54\d{9} ',                                 # +54 XXXXXXXXX
        r'0\d{7} ',                                    # 0XXXXXXX
        r'\+966\d{8} ',                                # +966 XXXXXXXX
        r'0\d{8}'                                      # 0XXXXXXXX
    ]

    # Check if the contact matches any of the patterns
        return any(re.match(pattern, contact) for pattern in patterns) is not None

def validate_contact_email(personal_data):
    contact = personal_data.get('contact', [])
    email = personal_data.get('email', [])
    
    valid_contact = is_valid_contact(contact) if contact != [] else False
    valid_email = is_valid_email(email) if email != [] else False

    invalid_contact = 'Invalid contact' if not valid_contact else 'Valid contact'
    invalid_email = 'Invalid email' if not valid_email else 'Valid email'
    
    return valid_contact, invalid_contact, valid_email, invalid_email

#Extracting the Data Using the Regex if the model don't extract Contact details
def extract_link_details(text):
    # Regex patterns    
    
    # Email regex
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    
    # URL and links regex, updated to avoid conflicts with email domains
    link_regex = re.compile(r'\b(?:https?:\/\/)?(?:www\.)[a-zA-Z0-9-]+\.(?:com|co\.in|co|io|org|net|edu|gov|mil|int|uk|us|in|de|au|app|tech|xyz|info|biz|fr|dev)\b')
    
    emails = email_regex.findall(text)

    links_RE = [link for link in link_regex.findall(text) if len(link)>=11]
    
    # Remove profile links that might conflict with emails
    links_RE = [link for link in links_RE if not any(email in link for email in emails)]
    
    return links_RE 

# For handling multiple data 
def normalize_data(value):
    """Replace empty lists with None and convert strings to lists."""
    if value == []:
        return None
    elif isinstance(value, str):  # check for str
        return [value]
    elif isinstance(value, (float, int)):  # Check for both float and int
        return [str(value)]
    return value
    
def process_resume_data(file_path):
    resume_text, hyperlinks = extract_text_based_on_format(file_path)
    print("Resume converted to text successfully.")
    
    if not resume_text:
        return {"error": "Text extraction failed"}
    
    # Extract LinkedIn and GitHub links
    linkedin_links, github_links = extract_links(hyperlinks)
    
    # Attempt to use Mistral model for parsing
    try:
        # Extract personal details using Mistral
        per_data = Model_PersonalDetails_Output(resume_text, client)
        print(f"Personal Data -----> {per_data}")
        
        # Extract professional details using Mistral
        pro_data = Model_ProfessionalDetails_Output(resume_text, client)
        print(f"Professional Data -----> {pro_data}")

        Edu_data=Model_EducationalDetails_Output(resume_text, client)
        print(f"Educational Data -----> {Edu_data}")
        
        # Extract link using Regular Expression 
        links = extract_link_details(resume_text)
        print(f"Links Data -----> {links}")
        
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
                "name": normalize_data(per_data.get('personal', {}).get('name', None)),
                "contact": normalize_data(per_data.get('personal', {}).get('contact_number', None)),
                "email": normalize_data(per_data.get('personal', {}).get('email', None)),
                "location": normalize_data(per_data.get('personal', {}).get('address', None)),
                "linkedin": normalize_data(linkedin_links),
                "github": normalize_data(github_links),
                "other_links": normalize_data(hyperlinks)
            },
            "professional": {
                "technical_skills": normalize_data(pro_data.get('professional', {}).get('technical_skills', None)),
                "non_technical_skills": normalize_data(pro_data.get('professional', {}).get('non_technical_skills', None)),
                "tools": normalize_data(pro_data.get('professional', {}).get('tools', None)),
                "experience": [
                    {
                        "company": normalize_data(pro_data.get('professional', {}).get('companies_worked_at', None)),
                        "projects": normalize_data(pro_data.get('professional', {}).get('projects', None)),
                        "role": normalize_data(pro_data.get('professional', {}).get('roles', None)),
                        "years": normalize_data(pro_data.get('professional', {}).get('experience', None)),
                        "project_experience": normalize_data(pro_data.get('professional', {}).get('projects_experience', None))
                    }
                ],
                "education": [
                    {
                        "qualification": normalize_data(Edu_data.get('educational', {}).get('qualifications', None)),
                        "university": normalize_data(Edu_data.get('educational', {}).get('university', None)),
                        "course": normalize_data(Edu_data.get('educational', {}).get('courses', None)),
                        "certificate": normalize_data(Edu_data.get('educational', {}).get('certifications', None))
                    }
                ]
            }
        }
              

        #Appending the list if any available as a text 
        if result['personal']['other_links'] is not None:
            result['personal']['other_links'] += links
            
        #Added the validator for details, Validate contact and email
        #valid_contact, invalid_contact, valid_email, invalid_email = validate_contact_email(result['personal'])
        #result['personal']['valid_contact'] = None
        #result['personal']['invalid_contact'] = None
        #result['personal']['valid_email'] = None
        #result['personal']['invalid_email'] = None
        
        #Appending the Educational Details if any available as a text        
        
        # If Mistral produces valid output, return it
        if per_data or pro_data:
            logging.info("Successfully extracted data using Mistral.")
            print(result)
            print("---------Mistral-------")
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
    print("---------SpaCy-------")
    return Parser_from_model(file_path)
    