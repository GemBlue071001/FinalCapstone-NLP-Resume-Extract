from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form, Depends
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import os
import logging
import requests
from pathlib import Path
import uvicorn
# from utils.error import handle_file_not_found, handle_invalid_file_type, handle_file_processing_error
from utils.spacy import Parser_from_model
from utils.mistral import process_resume_data, LMStudioClient

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from utils2 import JobMatchAnalyzer

from utils3 import VectorService, JobPost, SearchQuery

# Initialize FastAPI application
app = FastAPI(
    title="Resume Parser & CV-Job Matching API",
    description="Resume parsing application using LM Studio and SpaCy & API for analyzing match between CV and job postings",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resume Parser

# Configure application paths
UPLOAD_FOLDER = Path("uploads")
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'rsf', 'odt', 'png', 'jpg', 'jpeg'}

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key",
    max_age=3600  # 1 hour session
)

# LM Studio configuration
LM_STUDIO_URL = "http://192.168.2.38:7860/v1/chat/completions"
lm_studio_client = LMStudioClient(LM_STUDIO_URL)

def check_lm_studio_status():
    """Check if LM Studio server is running and responsive"""
    try:
        # Simple health check request
        response = requests.get("http://192.168.2.38:7860/v1/models")
        return response.status_code == 200
    except requests.RequestException:
        return False

async def get_lm_studio_client():
    """Dependency to get LM Studio client with status check"""
    if not check_lm_studio_status():
        raise HTTPException(
            status_code=503,
            detail="LM Studio server is not available. Please ensure the server is running."
        )
    return lm_studio_client

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    import time
    current_time = time.time()
    for file_path in UPLOAD_FOLDER.glob('*'):
        if current_time - file_path.stat().st_mtime > 3600:  # 1 hour
            try:
                file_path.unlink()
                logger.info(f"Cleaned up old file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {e}")

@app.on_event("startup")
async def startup_event():
    """Run startup tasks"""
    cleanup_old_files()
    logger.info("Application started, cleaned up old files")

@app.get("/")
async def index(request: Request):
    """API endpoint for index."""
    return JSONResponse(content={
        "status": "success",
        "message": "Welcome to Resume Parser API",
        "lm_studio_status": check_lm_studio_status(),
        "uploaded_file": request.session.get("uploaded_file")
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "lm_studio_available": check_lm_studio_status(),
        "upload_directory": str(UPLOAD_FOLDER),
        "allowed_extensions": list(ALLOWED_EXTENSIONS)
    }

@app.post("/upload_and_process")
async def upload_and_process(
    file: UploadFile = File(...),
    request: Request = None,
    lm_studio: LMStudioClient = Depends(get_lm_studio_client)
) -> Dict[str, Any]:
    """Handle file upload and process the file."""
    
    # Validate file
    if not file:
        raise HTTPException(status_code=400, detail="No file selected for upload")

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        # Clean up old files before new upload
        cleanup_old_files()

        # Save the uploaded file
        file_path = UPLOAD_FOLDER / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        logger.debug(f"File uploaded: {file.filename}")
        
        # Store file information in session
        request.session["uploaded_file"] = file.filename
        file_url = f"/uploads/{file.filename}"
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        request.session["file_url"] = file_url
        request.session["file_extension"] = file_extension

        # Process the file
        try:
            parsed_data = process_resume_data(str(file_path))
            if not parsed_data:
                raise ValueError("No data extracted from file")
            
            if 'error' in parsed_data:
                logger.error(f"Error in data parsing: {parsed_data['error']}")
                raise ValueError(parsed_data['error'])

        except Exception as e:
            logger.error(f"Error processing file with LM Studio: {str(e)}")
            # Fallback to SpaCy if LM Studio fails
            logger.info("Falling back to SpaCy parser")
            parsed_data = Parser_from_model(str(file_path))
            if not parsed_data or 'error' in parsed_data:
                raise ValueError("Both LM Studio and SpaCy parsing failed")

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
            'parser_used': 'lm_studio' if 'professional' in parsed_data else 'spacy',
            'message': 'Data processed and analyzed successfully'
        }

    except Exception as e:
        logger.error(f"File processing error: {str(e)}")
        # Clean up the uploaded file in case of error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove_file")
async def remove_file(request: Request):
    """Remove the uploaded file and reset the session."""
    uploaded_file = request.session.get("uploaded_file")
    if uploaded_file:
        file_path = UPLOAD_FOLDER / uploaded_file
        if file_path.exists():
            try:
                file_path.unlink()
                request.session.clear()
                return JSONResponse(content={
                    "status": "success",
                    "message": "File successfully removed",
                    "filename": uploaded_file
                })
            except Exception as e:
                logger.error(f"Error removing file: {str(e)}")
                raise HTTPException(status_code=500, detail="Error removing file")
    
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
    try:
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

        request.session.clear()
        response_data["details"]["session_cleared"] = True
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error in reset: {str(e)}")
        raise HTTPException(status_code=500, detail="Error resetting upload")

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
            "message": "Resource not found",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"Internal server error: {str(exc.detail)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else None
        }
    )

# CV-Job Matching API

# Global storage for CV and Job data
stored_data = {
    "cv_data": None,
    "job_data": None
}

# Initialize analyzer
analyzer = JobMatchAnalyzer()

class CVData(BaseModel):
    Data: List[Dict[str, Any]]
    success: bool = True

class JobData(BaseModel):
    id: int
    jobTitle: str
    jobDescription: str
    experienceRequired: int
    qualificationRequired: str
    skillSets: List[str]
    companyName: str
    jobType: Dict[str, Any]

@app.get("/")
async def root():
    return {
        "message": "CV-Job Matching API",
        "status": "active",
        "device": str(analyzer.device)
    }

@app.post("/upload_cv/")
async def upload_cv(cv_data: CVData):
    """Upload CV data"""
    try:
        stored_data["cv_data"] = cv_data.dict()
        return {
            "success": True,
            "message": "CV data stored successfully",
            "candidate_name": cv_data.Data[0]['personal']['name'][0] if cv_data.Data else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

@app.post("/upload_job/")
async def upload_job(job_data: JobData):
    """Upload Job Post data"""
    try:
        stored_data["job_data"] = job_data.dict()
        return {
            "success": True,
            "message": "Job data stored successfully",
            "job_title": job_data.jobTitle
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

@app.post("/analyze_match/")
async def analyze_match():
    """Analyze match using stored CV and Job data"""
    try:
        if not stored_data["cv_data"] or not stored_data["job_data"]:
            raise HTTPException(
                status_code=400,
                detail="Both CV and Job data must be uploaded first"
            )
            
        result = analyzer.analyze_match(
            cv_data=stored_data["cv_data"],
            job_data=stored_data["job_data"]
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": type(e).__name__
            }
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "loaded" if hasattr(analyzer, 'model') else "not_loaded",
        "device": str(analyzer.device),
        "stored_data": {
            "has_cv": stored_data["cv_data"] is not None,
            "has_job": stored_data["job_data"] is not None
        }
    }

@app.delete("/clear_data/")
async def clear_data():
    """Clear stored CV and Job data"""
    stored_data["cv_data"] = None
    stored_data["job_data"] = None
    return {
        "success": True,
        "message": "All stored data cleared"
    }

# Initialize vector service
vector_service = VectorService()

@app.post("/jobs/embed", 
         summary="Embed a job post",
         response_description="Job ID and success message")
async def embed_job(job: JobPost):
    """
    Embed a job post and save to database.
    
    - Takes a complete job post as input
    - Creates vector embedding using sentence transformer
    - Saves the embedding to PostgreSQL database
    """
    try:
        job_id = await vector_service.embed_job(job)
        if job_id:
            return {
                "message": "Job embedding updated successfully",
                "job_id": job_id
            }
        else:
            raise HTTPException(status_code=404, detail="Job not found")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating job embedding: {str(e)}"
        )

@app.post("/jobs/search",
         summary="Search for jobs",
         response_description="List of matching job IDs")
async def search_jobs(search_query: SearchQuery):
    """
    Search for jobs using semantic similarity.
    
    - Takes a natural language query
    - Returns IDs of most similar jobs
    - Example query: "jobs for data analysts in NY with remote options"
    """
    try:
        ids = await vector_service.search_jobs(search_query.query)
        return {"ids": ids}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching jobs: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )