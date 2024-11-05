import os
import re
import fitz
import logging
from PIL import Image
from pdf2image import convert_from_path
import platform
import pytesseract
import docx
from odf.opendocument import load as load_odt
from odf.text import P

# Path to tesseract executable (ensure it points to tesseract.exe)
#if platform.system() == "Windows":
#    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#else:
    # For Hugging Face Spaces or other Linux environments
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# # Set up logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler()]
# )

# # Path to Tesseract executable
# tesseract_path = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
# pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Function to extract text from PDF using PyMuPDF
def extract_text_from_pdf(file_path):
    text = ""
    hyperlinks = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")

            if not page_text.strip():
                images = convert_from_path(file_path, dpi=300)
                for image in images:
                    text += pytesseract.image_to_string(image)
            else:
                text += page_text

            links = page.get_links()
            for link in links:
                if link.get("uri"):
                    hyperlinks.append(link["uri"])
    except Exception as e:
        logging.error(f"Error extracting text or hyperlinks from PDF: {e}")
        return "", []
            
    return text, list(set(hyperlinks))

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {e}")
        return ""

# Function to extract text from RSF (assuming text-based format)
def extract_text_from_rsf(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error extracting text from RSF: {e}")
        return ""

# Function to extract text from ODT
def extract_text_from_odt(file_path):
    try:
        odt_doc = load_odt(file_path)
        text_elements = odt_doc.getElementsByType(P)
        text = "\n".join([te.firstChild.data for te in text_elements if te.firstChild])
        return text
    except Exception as e:
        logging.error(f"Error extracting text from ODT: {e}")
        return ""

# Function to extract text from images using Tesseract
def extract_text_from_image(file_path):
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        logging.error(f"Error extracting text from image: {e}")
        return ""

# Function to clean and preprocess the extracted text
def preprocess_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'(\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b)', r' \1 ', text)
    return text.strip()

# Function to automatically detect file format and extract text
def extract_text_based_on_format(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.pdf':
        text, hyperlinks = extract_text_from_pdf(file_path)
    elif file_ext == '.docx':
        text = extract_text_from_docx(file_path)
        hyperlinks = []
    elif file_ext == '.rsf':
        text = extract_text_from_rsf(file_path)
        hyperlinks = []
    elif file_ext == '.odt':
        text = extract_text_from_odt(file_path)
        hyperlinks = []
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        text = extract_text_from_image(file_path)
        hyperlinks = []
    else:
        raise ValueError("Unsupported file format")

    return text, hyperlinks
