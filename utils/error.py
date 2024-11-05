import logging
from flask import render_template, request

# Set up logging for errors
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# File handler for logging errors to a file
file_handler = logging.FileHandler('app_error.log')
file_handler.setLevel(logging.ERROR)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler for logging errors to the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 404 Error Handler
def page_not_found(e):
    logger.error(f"404 Error: {request.url}")
    return render_template('404.html'), 404

# 500 Error Handler
def internal_server_error(e):
    logger.error(f"500 Error: {e}, URL: {request.url}")
    return render_template('500.html'), 500

# File Not Found Error Handler
def handle_file_not_found():
    logger.error("File not found.")
    return render_template('error.html', message="The file you are looking for does not exist."), 404

# Invalid File Type Error Handler
def handle_invalid_file_type():
    logger.error("Invalid file type.")
    return render_template('error.html', message="Invalid file type. Allowed types: pdf, docx, rsf, odt, png, jpg, jpeg."), 400

# File Processing Error Handler
def handle_file_processing_error():
    logger.error("File processing failed.")
    return render_template('error.html', message="Failed to process the file."), 500
