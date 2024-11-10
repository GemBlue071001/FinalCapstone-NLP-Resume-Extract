import spacy
import logging
import json
from utils.fileTotext import extract_text_based_on_format
import re

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
        r'0\d{8}'                                     # 0XXXXXXXX
    ]

    # Check if the contact matches any of the patterns
        return any(re.match(pattern, contact) for pattern in patterns) is not None

# Extracting the Contact Details through Regular Expression 
def extract_contact_details(text):
    # Regex patterns
    # Phone numbers with at least 5 digits in any segment 
    combined_phone_regex = re.compile(r'''
    (?: 
        #(?:(?:\+91[-.\s]?)?\d{5}[-.\s]?\d{5})|(?:\+?\d{1,3})?[-.\s()]?\d{5,}[-.\s()]?\d{5,}[-.\s()]?\d{1,9} | /^[\.-)( ]*([0-9]{3})[\.-)( ]*([0-9]{3})[\.-)( ]*([0-9]{4})$/ |
        \+1\s\(\d{3}\)\s\d{3}-\d{4} |               # USA/Canada Intl +1 (XXX) XXX-XXXX
        \(\d{3}\)\s\d{3}-\d{4} |                    # USA/Canada STD (XXX) XXX-XXXX
        \(\d{3}\)\s\d{3}\s\d{4} |                   # USA/Canada (XXX) XXX XXXX
        \(\d{3}\)\s\d{3}\s\d{3} |                   # USA/Canada (XXX) XXX XXX
        \+1\d{10} |                                 # +1 XXXXXXXXXX
        \d{10} |                                    # XXXXXXXXXX
        \+44\s\d{4}\s\d{6} |                        # UK Intl +44 XXXX XXXXXX
        \+44\s\d{3}\s\d{3}\s\d{4} |                 # UK Intl +44 XXX XXX XXXX
        0\d{4}\s\d{6} |                             # UK STD 0XXXX XXXXXX
        0\d{3}\s\d{3}\s\d{4} |                      # UK STD 0XXX XXX XXXX
        \+44\d{10} |                                # +44 XXXXXXXXXX
        0\d{10} |                                   # 0XXXXXXXXXX
        \+61\s\d\s\d{4}\s\d{4} |                    # Australia Intl +61 X XXXX XXXX
        0\d\s\d{4}\s\d{4} |                         # Australia STD 0X XXXX XXXX
        \+61\d{9} |                                 # +61 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+91\s\d{5}-\d{5} |                         # India Intl +91 XXXXX-XXXXX
        \+91\s\d{4}-\d{6} |                         # India Intl +91 XXXX-XXXXXX
        \+91\s\d{10} |                              # India Intl +91 XXXXXXXXXX
        \+91\s\d{3}\s\d{3}\s\d{4} |                 # India Intl +91 XXX XXX XXXX
        \+91\s\d{3}-\d{3}-\d{4} |                   # India Intl +91 XXX-XXX-XXXX
        \+91\s\d{2}\s\d{4}\s\d{4} |                 # India Intl +91 XX XXXX XXXX
        \+91\s\d{2}-\d{4}-\d{4} |                   # India Intl +91 XX-XXXX-XXXX
        \+91\s\d{5}\s\d{5} |                        # India Intl +91 XXXXX XXXXX 
        \d{5}\s\d{5} |                              # India XXXXX XXXXX 
        \d{5}-\d{5} |                               # India XXXXX-XXXXX 
        0\d{2}-\d{7} |                              # India STD 0XX-XXXXXXX
        \+91\d{10} |                                # +91 XXXXXXXXXX
        \d{10} |                                    # XXXXXXXXXX   # Here is the regex to handle all possible combination of the contact
        \d{6}-\d{4} |                               # XXXXXX-XXXX
        \d{4}-\d{6} |                               # XXXX-XXXXXX
        \d{3}\s\d{3}\s\d{4} |                       # XXX XXX XXXX
        \d{3}-\d{3}-\d{4} |                         # XXX-XXX-XXXX
        \d{4}\s\d{3}\s\d{3} |                       # XXXX XXX XXX
        \d{4}-\d{3}-\d{3} |                         # XXXX-XXX-XXX #-----
        \+49\s\d{4}\s\d{8} |                        # Germany Intl +49 XXXX XXXXXXXX
        \+49\s\d{3}\s\d{7} |                        # Germany Intl +49 XXX XXXXXXX
        0\d{3}\s\d{8} |                             # Germany STD 0XXX XXXXXXXX
        \+49\d{12} |                                # +49 XXXXXXXXXXXX
        \+49\d{10} |                                # +49 XXXXXXXXXX
        0\d{11} |                                   # 0XXXXXXXXXXX
        \+86\s\d{3}\s\d{4}\s\d{4} |                 # China Intl +86 XXX XXXX XXXX
        0\d{3}\s\d{4}\s\d{4} |                      # China STD 0XXX XXXX XXXX
        \+86\d{11} |                                # +86 XXXXXXXXXXX
        \+81\s\d\s\d{4}\s\d{4} |                    # Japan Intl +81 X XXXX XXXX
        \+81\s\d{2}\s\d{4}\s\d{4} |                 # Japan Intl +81 XX XXXX XXXX
        0\d\s\d{4}\s\d{4} |                         # Japan STD 0X XXXX XXXX
        \+81\d{10} |                                # +81 XXXXXXXXXX
        \+81\d{9} |                                 # +81 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+55\s\d{2}\s\d{5}-\d{4} |                  # Brazil Intl +55 XX XXXXX-XXXX
        \+55\s\d{2}\s\d{4}-\d{4} |                  # Brazil Intl +55 XX XXXX-XXXX
        0\d{2}\s\d{4}\s\d{4} |                      # Brazil STD 0XX XXXX XXXX
        \+55\d{11} |                                # +55 XXXXXXXXXXX
        \+55\d{10} |                                # +55 XXXXXXXXXX
        0\d{10} |                                   # 0XXXXXXXXXX
        \+33\s\d\s\d{2}\s\d{2}\s\d{2}\s\d{2} |      # France Intl +33 X XX XX XX XX
        0\d\s\d{2}\s\d{2}\s\d{2}\s\d{2} |           # France STD 0X XX XX XX XX
        \+33\d{9} |                                 # +33 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+7\s\d{3}\s\d{3}-\d{2}-\d{2} |             # Russia Intl +7 XXX XXX-XX-XX
        8\s\d{3}\s\d{3}-\d{2}-\d{2} |               # Russia STD 8 XXX XXX-XX-XX
        \+7\d{10} |                                 # +7 XXXXXXXXXX
        8\d{10} |                                   # 8 XXXXXXXXXX
        \+27\s\d{2}\s\d{3}\s\d{4} |                 # South Africa Intl +27 XX XXX XXXX
        0\d{2}\s\d{3}\s\d{4} |                      # South Africa STD 0XX XXX XXXX
        \+27\d{9} |                                 # +27 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+52\s\d{3}\s\d{3}\s\d{4} |                 # Mexico Intl +52 XXX XXX XXXX
        \+52\s\d{2}\s\d{4}\s\d{4} |                 # Mexico Intl +52 XX XXXX XXXX
        01\s\d{3}\s\d{4} |                          # Mexico STD 01 XXX XXXX
        \+52\d{10} |                                # +52 XXXXXXXXXX
        01\d{7} |                                   # 01 XXXXXXX
        \+234\s\d{3}\s\d{3}\s\d{4} |                # Nigeria Intl +234 XXX XXX XXXX
        0\d{3}\s\d{3}\s\d{4} |                      # Nigeria STD 0XXX XXX XXXX
        \+234\d{10} |                               # +234 XXXXXXXXXX
        0\d{10} |                                   # 0XXXXXXXXXX
        \+971\s\d\s\d{3}\s\d{4} |                   # UAE Intl +971 X XXX XXXX
        0\d\s\d{3}\s\d{4} |                         # UAE STD 0X XXX XXXX
        \+971\d{8} |                                # +971 XXXXXXXX
        0\d{8} |                                    # 0XXXXXXXX
        \+54\s9\s\d{3}\s\d{3}\s\d{4} |              # Argentina Intl +54 9 XXX XXX XXXX
        \+54\s\d{1}\s\d{4}\s\d{4} |                 # Argentina Intl +54 X XXXX XXXX
        0\d{3}\s\d{4} |                             # Argentina STD 0XXX XXXX
        \+54\d{10} |                                # +54 9 XXXXXXXXXX
        \+54\d{9} |                                 # +54 XXXXXXXXX
        0\d{7} |                                    # 0XXXXXXX
        \+966\s\d\s\d{3}\s\d{4} |                   # Saudi Intl +966 X XXX XXXX
        0\d\s\d{3}\s\d{4} |                         # Saudi STD 0X XXX XXXX
        \+966\d{8} |                                # +966 XXXXXXXX
        0\d{8} |                                    # 0XXXXXXXX
        \+1\d{10} |                                 # +1 XXXXXXXXXX
        \+1\s\d{3}\s\d{3}\s\d{4} |                  # +1 XXX XXX XXXX
        \d{5}\s\d{5} |                              # XXXXX XXXXX                              
        \d{10} |                                    # XXXXXXXXXX
        \+44\d{10} |                                # +44 XXXXXXXXXX
        0\d{10} |                                   # 0XXXXXXXXXX
        \+61\d{9} |                                 # +61 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+91\d{10} |                                # +91 XXXXXXXXXX
        \+49\d{12} |                                # +49 XXXXXXXXXXXX
        \+49\d{10} |                                # +49 XXXXXXXXXX
        0\d{11} |                                   # 0XXXXXXXXXXX
        \+86\d{11} |                                # +86 XXXXXXXXXXX
        \+81\d{10} |                                # +81 XXXXXXXXXX
        \+81\d{9} |                                 # +81 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+55\d{11} |                                # +55 XXXXXXXXXXX
        \+55\d{10} |                                # +55 XXXXXXXXXX
        0\d{10} |                                   # 0XXXXXXXXXX
        \+33\d{9} |                                 # +33 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX
        \+7\d{10} |                                 # +7 XXXXXXXXXX
        8\d{10} |                                   # 8 XXXXXXXXXX
        \+27\d{9} |                                 # +27 XXXXXXXXX
        0\d{9} |                                    # 0XXXXXXXXX (South Africa STD)
        \+52\d{10} |                                # +52 XXXXXXXXXX
        01\d{7} |                                   # 01 XXXXXXX
        \+234\d{10} |                               # +234 XXXXXXXXXX
        0\d{10} |                                   # 0XXXXXXXXXX
        \+971\d{8} |                                # +971 XXXXXXXX
        0\d{8} |                                    # 0XXXXXXXX
        \+54\s9\s\d{10} |                           # +54 9 XXXXXXXXXX
        \+54\d{9} |                                 # +54 XXXXXXXXX
        0\d{7} |                                    # 0XXXXXXX
        \+966\d{8} |                                # +966 XXXXXXXX
        0\d{8}                                      # 0XXXXXXXX
        \+\d{3}-\d{3}-\d{4}
    )  
    ''',re.VERBOSE)
    
    # Email regex
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    
    # URL and links regex, updated to avoid conflicts with email domains
    link_regex = re.compile(r'\b(?:https?:\/\/)?(?:www\.)[a-zA-Z0-9-]+\.(?:com|co\.in|co|io|org|net|edu|gov|mil|int|uk|us|in|de|au|app|tech|xyz|info|biz|fr|dev)\b')
    
    # Find all matches in the text
    phone_numbers = [num for num in combined_phone_regex.findall(text) if len(num) >= 5]
    
    emails = email_regex.findall(text)

    links_RE = [link for link in link_regex.findall(text) if len(link)>=11]
    
    # Remove profile links that might conflict with emails
    links_RE = [link for link in links_RE if not any(email in link for email in emails)]
    
    return {
        "phone_numbers": phone_numbers,
        "emails": emails,
        "links_RE": links_RE
    }  

# preprocessing the data 
def process_extracted_text(extracted_text):
    # Load JSON data
    data = json.dumps(extracted_text, indent=4)
    data = json.loads(data)

    # Create a single dictionary to hold combined results
    combined_results = {
        "phone_numbers": [],
        "emails": [],
        "links_RE": []
    }

    # Process each text entry
    for filename, text in data.items():
        contact_details = extract_contact_details(text)
        # Extend combined results with the details from this file
        combined_results["phone_numbers"].extend(contact_details["phone_numbers"])
        combined_results["emails"].extend(contact_details["emails"])
        combined_results["links_RE"].extend(contact_details["links_RE"])

    # Convert the combined results to JSON
    #combined_results_json = json.dumps(combined_results, indent=4)
    combined_results_json = combined_results

    # Print the final JSON results
    print("Combined contact details in JSON format:")
    print(combined_results_json)

    return combined_results_json 

# Function to parse resume with SpaCy

def Parser_from_model(file_path):
    # Initialize result with lists instead of strings for consistency
    result = {
        "personal": {
            "name": [],
            "contact": [],
            "email": [],
            "location": [],
            "link": []               
        },
        "professional": {
            "technical_skills": [],
            "non_technical_skills": [],
            "tools": [],
            "experience": [
                {
                    "company": [],
                    "projects": [],
                    "role": [],
                    "years": [],
                    "project_experience": []
                }
            ],
            "education": [
                {
                    "qualification": [],
                    "university": [],
                    "course": [],
                    "certificate": []
                }
            ]
        }
    }

    try:
        nlp = spacy.load("Spacy_Models/ner_model_05_3")
        logging.debug("Model loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        return {"error": "Model loading failed"}

    try:
        cleaned_text, hyperlinks = extract_text_based_on_format(file_path)
        if not cleaned_text.strip():
            logging.error("No text extracted from the file.")
            return {"error": "Text extraction failed"}
    except Exception as e:
        logging.error(f"Error extracting text from file: {e}")
        return {"error": "Text extraction failed"}

    try:
        doc = nlp(cleaned_text)
    except Exception as e:
        logging.error(f"Error processing text with SpaCy: {e}")
        return {"error": "Text processing failed"}

    # Extracting Contact Details
    cont_data = process_extracted_text(cleaned_text)

    # Initialize entities as a dictionary with lists
    entities = {label: [] for label in [
        'PERSON', 'EMAIL', 'CONTACT', 'LOCATION', 'SKILL', 'SOFT_SKILL', 
        'COMPANY', 'PROJECTS', 'JOB_TITLE', 'YEARS_EXPERIENCE', 'EXPERIENCE', 
        'QUALIFICATION', 'UNIVERSITY', 'COURSE', 'CERTIFICATE'
    ]}

    # Process entities and avoid duplicates
    for ent in doc.ents:
        if ent.label_ in entities and ent.text not in entities[ent.label_]:
            entities[ent.label_].append(ent.text)

    # Helper function to handle None or unexpected types
    def normalize_to_list(value):
        if value is []:
            return None
        elif isinstance(value, (str, int, float)):
            return [str(value)]
        elif isinstance(value, list):
            return value
        else:
            return [str(value)]

    # Map entities to result JSON
    result['personal']['name'] = normalize_to_list(entities.get('PERSON'))
    result['personal']['email'] += cont_data['emails']
    

    # Validate email and handle invalid ones
    for email in entities.get('EMAIL', []):
        if is_valid_email(email):
            result['personal']['email'].append(email)        

    # Validate contact and handle invalid ones
    result['personal']['contact'] += cont_data['phone_numbers']
    for contact in entities.get('CONTACT', []):
        if is_valid_contact(contact):
            result['personal']['contact'].append(contact)  

    result['personal']['location'] = normalize_to_list(entities.get('LOCATION'))
    result['personal']['link'] = normalize_to_list(hyperlinks)
    result['personal']['link'] += cont_data['links_RE'] 

    result['professional']['technical_skills'] = normalize_to_list(entities.get('SKILL'))
    result['professional']['non_technical_skills'] = normalize_to_list(entities.get('SOFT_SKILL'))
    result['professional']['tools'] = None  # Logic for tools can be added if needed

    experience = result['professional']['experience'][0]
    experience['company'] = normalize_to_list(entities.get('COMPANY'))
    experience['projects'] = normalize_to_list(entities.get('PROJECTS'))
    experience['role'] = normalize_to_list(entities.get('JOB_TITLE'))
    experience['years'] = normalize_to_list(entities.get('YEARS_EXPERIENCE'))
    experience['project_experience'] = normalize_to_list(entities.get('EXPERIENCE'))

    education = result['professional']['education'][0]
    education['qualification'] = normalize_to_list(entities.get('QUALIFICATION'))
    education['university'] = normalize_to_list(entities.get('UNIVERSITY'))
    education['course'] = normalize_to_list(entities.get('COURSE'))
    education['certificate'] = normalize_to_list(entities.get('CERTIFICATE'))

    print(result)
    return result