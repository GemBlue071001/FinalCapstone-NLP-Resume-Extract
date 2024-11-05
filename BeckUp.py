from flask import Flask, request, redirect, flash, session, render_template, url_for
import os
import json
from werkzeug.utils import secure_filename
import logging
from utils.error import handle_file_not_found, handle_invalid_file_type, handle_file_processing_error, page_not_found, internal_server_error
from utils.spacy import Parser_from_model
from utils.mistral import process_resume_data
import platform
from waitress import serve

if platform.system() == "Windows":
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'
    app.config['UPLOAD_FOLDER'] = 'uploads'
# else:
#     # For Hugging Face Spaces or other Linux environments
#     if __name__ != "__main__":
#     serve(app, host="0.0.0.0", port=7860)


# Error handlers
app.register_error_handler(404, page_not_found)
app.register_error_handler(500, internal_server_error)

# Allowed extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'rsf', 'odt', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    uploaded_file = session.get('uploaded_file', None)
    return render_template('index.html', uploaded_file=uploaded_file)

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         flash('No file part')
#         return redirect(request.url)
    
#     file = request.files['file']

#     if file.filename == '':
#         flash('No selected file')
#         return redirect(request.url)

#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         logging.debug(f"File uploaded: {filename}")
#         session['uploaded_file'] = filename
#         flash('File successfully uploaded')
#         return redirect(url_for('index'))
#     else:
#         return handle_invalid_file_type()

# def process_file():
#     selected_file = session.get('uploaded_file')
#     if not selected_file:
#         flash('No file selected for processing')
#         return redirect(url_for('index'))

#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)
#     if not os.path.exists(file_path):
#         return handle_file_not_found()
#     parsed_data = process_resume_data(file_path)
#     if not parsed_data or 'error' in parsed_data:
#         return handle_file_processing_error()

#     session['processed_data'] = parsed_data
#     flash('Data processed successfully')
#     return redirect(url_for('result'))

@app.route('/upload_and_process', methods=['POST', 'GET'])
def upload_and_process():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        logging.debug(f"File uploaded: {filename}")
        session['uploaded_file'] = filename

        # Process the file after uploading
        parsed_data = process_resume_data(file_path)
        if not parsed_data or 'error' in parsed_data:
            return handle_file_processing_error()

        session['processed_data'] = parsed_data
        flash('File uploaded and data processed successfully')
        return redirect(url_for('result'))
    else:
        return handle_invalid_file_type()



@app.route('/remove_file')
def remove_file():
    uploaded_file = session.get('uploaded_file')
    if uploaded_file:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file))
        session.pop('uploaded_file', None)
        flash('File successfully removed')
    return redirect(url_for('index'))

@app.route('/reset_upload')
def reset_upload():
    uploaded_file = session.get('uploaded_file')
    if uploaded_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        session.pop('uploaded_file', None)
    
    session.pop('processed_data', None)
    flash('File reset. You can upload a new file.')
    return redirect(url_for('index'))

# @app.route('/process', methods=['GET', 'POST'])
# def process_file():
#     selected_file = session.get('uploaded_file')
#     if not selected_file:
#         flash('No file selected for processing')
#         return redirect(url_for('index'))

#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)
#     if not os.path.exists(file_path):
#         return handle_file_not_found()
#     parsed_data = process_resume_data(file_path)
#     if not parsed_data or 'error' in parsed_data:
#         return handle_file_processing_error()

#     session['processed_data'] = parsed_data
#     flash('Data processed successfully')
#     return redirect(url_for('result'))

@app.route('/loading')
def loading():
    selected_file = session.get('uploaded_file')
    if not selected_file:
        flash('No file selected for processing')
        return redirect(url_for('index'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)

    parsed_data = process_resume_data(file_path)
    
    if parsed_data and 'error' not in parsed_data:
        session['processed_data'] = json.loads(parsed_data)
        flash('Data processed successfully')
        return redirect(url_for('result'))
    else:
        return handle_file_processing_error()

@app.route('/result')
def result():
    processed_data = session.get('processed_data', None)
    if not processed_data:
        flash('No data to display. Please upload and process a file.')
        return redirect(url_for('index'))

    return render_template('result.html', parsed_data=processed_data)

if __name__ == '__main__':
    app.run(debug=True)
