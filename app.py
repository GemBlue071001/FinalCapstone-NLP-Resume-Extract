# from flask import Flask, request, redirect, flash, session, render_template, url_for, send_from_directory, jsonify
# import os
# import json
# import logging
# from werkzeug.utils import secure_filename
# from utils.error import handle_file_not_found, handle_invalid_file_type, handle_file_processing_error, page_not_found, internal_server_error
# from utils.spacy import Parser_from_model
# from utils.mistral import process_resume_data
# import platform
# from waitress import serve

# # Initialize the Flask application
# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# app.config['UPLOAD_FOLDER'] = 'uploads/'
# UPLOAD_FOLDER = 'uploads/'

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# if not os.path.exists(app.config['UPLOAD_FOLDER']):
#     os.makedirs(app.config['UPLOAD_FOLDER'])

# # Allowed file extensions
# ALLOWED_EXTENSIONS = {'pdf', 'docx', 'rsf', 'odt', 'png', 'jpg', 'jpeg'}

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)

# # Error handlers
# app.register_error_handler(404, page_not_found)
# app.register_error_handler(500, internal_server_error)

# def allowed_file(filename):
#     """Check if the file has an allowed extension."""
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/')
# def index():
#     """Display the index page with the uploaded file information."""
#     uploaded_file = session.get('uploaded_file', None)
#     return render_template('index.html', uploaded_file=uploaded_file)

# @app.route('/upload_and_process', methods=['POST'])
# def upload_and_process():
#     """Handle file upload and process the file."""
#     if 'file' not in request.files or request.files['file'].filename == '':
#         flash('No file selected for upload.')
#         return jsonify({'message': "No file selected for upload."})

#     file = request.files['file']
    
#     # Check if the file is allowed
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(file_path)
#         print(f"file path --->{file_path}")
#         logging.debug(f"File uploaded: {filename}")
#         session['uploaded_file'] = filename

#         file_url = f"/uploads/{filename}"        
#         file_extension = filename.rsplit('.', 1)[1].lower()
#         print(f"File URL: {file_url}, File Extension: {file_extension}")
#         session['file_url'] = file_url
#         session['file_extension'] = file_extension

#         # Process the file after uploading
#         try:
#             parsed_data = process_resume_data(file_path)
#             if not parsed_data or 'error' in parsed_data:
#                 flash('An error occurred during file processing.')
#                 return jsonify({'message': "An error occurred during file processing."})

#             print("file path of files---->",file_path)
#             session['processed_data'] = parsed_data
#             session['file_path'] = file_path
#             flash('File uploaded and data processed successfully.')
#             return jsonify({
#                             'Data': [parsed_data], 
#                             'process_file': f"https://webashalarforml-resumeextractor3.hf.space/{file_path}", 
#                             'success': True, 
#                             'message': 'Data processed and analyzed successfully'
#                             })

#         except Exception as e:
#             logging.error(f"File processing error: {str(e)}")
#             flash('An error occurred while processing the file.')
#             return jsonify({'message': "An error occurred while processing the file. Cannot generate results"})
#     else:
#         return jsonify({'message': "File type not allowed."})

# @app.route('/remove_file', methods=['POST'])
# def remove_file():
#     """Remove the uploaded file and reset the session."""
#     uploaded_file = session.get('uploaded_file')
#     if uploaded_file:
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file)
#         if os.path.exists(file_path):
#             os.remove(file_path)
#         session.pop('uploaded_file', None)
#         flash('File successfully removed.')
#     else:
#         flash('No file to remove.')
#     return redirect(url_for('index'))

# @app.route('/reset_upload')
# def reset_upload():
#     """Reset the uploaded file and the processed data."""
#     uploaded_file = session.get('uploaded_file')
#     if uploaded_file:
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file)
#         if os.path.exists(file_path):
#             os.remove(file_path)
#         session.pop('uploaded_file', None)

#     session.pop('processed_data', None)
#     flash('File and data reset. You can upload a new file.')
#     return redirect(url_for('index'))

# @app.route('/result')
# def result():
#     """Display the processed data result."""
#     processed_data = session.get('processed_data', None)
#     file_url = session.get('file_url', None)
#     file_extension = session.get('file_extension', None)
#     uploaded_file = session.get('uploaded_file', None)
#     file_path = session.get('file_path', None)
#     if not processed_data:
#         flash('No data to display. Please upload and process a file.')
#         return redirect(url_for('index'))
#     return render_template('result.html', parsed_data=processed_data, file_url=file_url, file_extension=file_extension, file_path=file_path)

# # Route to serve uploaded files
# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# if __name__ == '__main__':
#     # For Windows development
#     if platform.system() == "Windows":
#         app.run(debug=True)
#     # For Linux or production with Waitress
#     else:
#         serve(app, host="0.0.0.0", port=7860)

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional, Dict, Any
import os
import logging
from pathlib import Path
import uvicorn
from utils.error import handle_file_not_found, handle_invalid_file_type, handle_file_processing_error
from utils.spacy import Parser_from_model
from utils.mistral import process_resume_data

# Initialize FastAPI application
app = FastAPI(title="Resume Parser")

# Configure application
UPLOAD_FOLDER = Path("uploads")
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'rsf', 'odt', 'png', 'jpg', 'jpeg'}

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key"
)

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.get("/")
async def index(request: Request):
    """API endpoint for index."""
    return JSONResponse(content={
        "status": "success",
        "message": "Welcome to Resume Parser API",
        "uploaded_file": request.session.get("uploaded_file")
    })

@app.post("/upload_and_process")
async def upload_and_process(
    file: UploadFile = File(...),
    request: Request = None
) -> Dict[str, Any]:
    """Handle file upload and process the file."""
    if not file:
        raise HTTPException(status_code=400, detail="No file selected for upload")

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        # Save the uploaded file
        file_path = UPLOAD_FOLDER / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logging.debug(f"File uploaded: {file.filename}")
        
        # Store file information in session
        request.session["uploaded_file"] = file.filename
        file_url = f"/uploads/{file.filename}"
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        request.session["file_url"] = file_url
        request.session["file_extension"] = file_extension

        # Process the file
        parsed_data = process_resume_data(str(file_path))
        if not parsed_data or 'error' in parsed_data:
            raise HTTPException(status_code=500, detail="Error processing file")

        request.session["processed_data"] = parsed_data
        request.session["file_path"] = str(file_path)

        return {
            'status': 'success',
            'data': parsed_data,
            'file_info': {
                'filename': file.filename,
                'file_url': file_url,
                'file_type': file_extension
            },
            'process_file': f"https://webashalarforml-resumeextractor3.hf.space/{file_path}",
            'message': 'Data processed and analyzed successfully'
        }

    except Exception as e:
        logging.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove_file")
async def remove_file(request: Request):
    """Remove the uploaded file and reset the session."""
    uploaded_file = request.session.get("uploaded_file")
    if uploaded_file:
        file_path = UPLOAD_FOLDER / uploaded_file
        if file_path.exists():
            file_path.unlink()
        request.session.pop("uploaded_file", None)
        return JSONResponse(content={
            "status": "success",
            "message": "File successfully removed",
            "filename": uploaded_file
        })
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "No file to remove"
        }
    )

@app.get("/reset_upload")
async def reset_upload(request: Request):
    """Reset the uploaded file and the processed data."""
    uploaded_file = request.session.get("uploaded_file")
    response_data = {
        "status": "success",
        "message": "Reset completed",
        "details": {}
    }

    if uploaded_file:
        file_path = UPLOAD_FOLDER / uploaded_file
        if file_path.exists():
            file_path.unlink()
            response_data["details"]["file_removed"] = uploaded_file
        request.session.pop("uploaded_file", None)
        request.session.pop("processed_data", None)
        response_data["details"]["session_cleared"] = True

    return JSONResponse(content=response_data)

@app.get("/result")
async def result(request: Request):
    """Get the processed data result."""
    processed_data = request.session.get("processed_data")
    if not processed_data:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "No processed data found"
            }
        )
    
    return JSONResponse(content={
        "status": "success",
        "data": processed_data,
        "file_info": {
            "file_url": request.session.get("file_url"),
            "file_extension": request.session.get("file_extension"),
            "file_path": request.session.get("file_path")
        }
    })

# Exception handlers
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Resource not found"
        }
    )

@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else None
        }
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=7860, reload=True)