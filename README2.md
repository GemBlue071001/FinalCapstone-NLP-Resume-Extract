_\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_
_\\----------- **Resume Parser** ----------\\_
_\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\_

cd C:\My Station\Final\ResumeExtractor-FinalCapstone\ResumeExtractor3
conda activate resume_extractor_3

# Overview:
This project is a comprehensive Resume Parsing tool built using Python,
integrating the Mistral-Nemo-Instruct-2407 model for primary parsing.
If Mistral fails or encounters issues,
the system falls back to a custom-trained spaCy model to ensure continued functionality.
The tool is wrapped with a Flask API and has a user interface built using HTML and CSS.


# Installation Guide:

1. Create and Activate a Virtual Environment
    python -m venv venv
    source venv/bin/activate  # For Linux/Mac
    # or
    venv\Scripts\activate  # For Windows

    # NOTE: If the virtual environment (venv) is already created, you can skip the creation step and just activate.
        - For Linux/Mac:
            source venv/bin/activate
        - For Windows:
            venv\Scripts\activate

2. Install Required Libraries
    pip install -r requirements.txt

    # Ensure the following dependencies are included:
    - Flask
    - spaCy
    - huggingface_hub
    - PyMuPDF
    - python-docx
    - Tesseract-OCR (for image-based parsing)

3. Set up Hugging Face Token
    - Add your Hugging Face token to the .env file as:
    HF_TOKEN=<your_huggingface_token>


# File Structure Overview:
    Mistral_With_Spacy/
    │
    ├── Spacy_Models/
    │   └── ner_model_05_3  # Pretrained spaCy model directory for resume parsing
    │
    ├── templates/
    │   ├── index.html  # UI for file upload
    │   └── result.html  # Display parsed results in structured JSON
    │
    ├── uploads/  # Directory for uploaded resume files
    │
    ├── utils/
    │   ├── mistral.py  # Code for calling Mistral API and handling responses
    │   ├── spacy.py  # spaCy fallback model for parsing resumes
    │   ├── error.py  # Error handling utilities
    │   └── fileTotext.py  # Functions to extract text from different file formats (PDF, DOCX, etc.)
    │
    ├── venv/  # Virtual environment
    │
    ├── .env  # Environment variables file (contains Hugging Face token)
    │
    ├── main.py  # Flask app handling API routes for uploading and processing resumes
    │
    └── requirements.txt  # Dependencies required for the project


# Program Overview:

    # Mistral Integration (utils/mistral.py)
        - Mistral API Calls: Uses Hugging Face’s Mistral-Nemo-Instruct-2407 model to parse resumes.
        - Personal and Professional Extraction: Two functions extract personal and professional information in structured JSON format.
        - Fallback Mechanism: If Mistral fails, spaCy NER model is used as a fallback.

    # SpaCy Integration (utils/spacy.py)
        - Custom Trained Model: Uses a spaCy model (ner_model_05_3) trained specifically for resume parsing.
        - Named Entity Recognition: Extracts key information like Name, Email, Contact, Location, Skills, Experience, etc., from resumes.
        - Validation: Includes validation for extracted emails and contacts.

    # File Conversion (utils/fileTotext.py)
       - Text Extraction: Handles different resume formats (PDF, DOCX, ODT, RSF, and images like PNG, JPG, JPEG) and extracts text for further processing.
          - PDF Files: Uses PyMuPDF to extract text and, if necessary, Tesseract-OCR for image-based PDF content.
          - DOCX Files: Uses `python-docx` to extract structured text from Word documents.
          - ODT Files: Uses `odfpy` to extract text from ODT (OpenDocument) files.
          - RSF Files: Reads plain text from RSF files.
          - Images (PNG, JPG, JPEG): Uses Tesseract-OCR to extract text from image-based resumes.

       - Hyperlink Extraction: Extracts hyperlinks from PDF files, capturing any embedded URLs during the parsing process.


    # Error Handling (utils/error.py)
        - Handles API response errors, file format errors, and ensures smooth fallbacks without crashing the app.

    # Flask API (main.py)
        Endpoints:
        - /upload for uploading resumes.
        - Displays parsed results in JSON format on the results page.
        - UI: Simple interface for uploading resumes and viewing the parsing results.


# Tree map of your program:

    main.py
    ├── Handles API side
    ├── File upload/remove
    ├── Process resumes
    └── Show result

    utils
    ├── fileTotext.py
    │   └── Converts files to text
    │       ├── PDF
    │       ├── DOCX
    │       ├── RTF
    │       ├── ODT
    │       ├── PNG
    │       ├── JPG
    │       └── JPEG
    ├── mistral.py
    │   ├── Mistral API Calls
    │   │   └── Uses Mistral-Nemo-Instruct-2407 model
    │   ├── Personal and Professional Extraction
    │   │   ├── Extracts personal information
    │   │   └── Extracts professional information
    │   └── Fallback Mechanism
    │       └── Uses spaCy NER model if Mistral fails
    └── spacy.py
        ├── Custom Trained Model
        │   └── Uses spaCy model (ner_model_05_3)
        ├── Named Entity Recognition
        │   └── Extracts key information (Name, Email, Contact, etc.)
        └── Validation
            └── Validates emails and contacts


# References:

- [Flask Documentation](https://flask.palletsprojects.com/)
- [spaCy Documentation](https://spacy.io/usage)
- [Hugging Face Hub API](https://huggingface.co/docs/huggingface_hub/index)
- [PyMuPDF (MuPDF) Documentation](https://pymupdf.readthedocs.io/en/latest/)
- [python-docx Documentation](https://python-docx.readthedocs.io/en/latest/)
- [Tesseract OCR Documentation](https://github.com/tesseract-ocr/tesseract)
- [Virtual Environments in Python](https://docs.python.org/3/tutorial/venv.html)
