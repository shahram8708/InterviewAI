"""
Service for processing resumes.
"""
import os
import io
import logging
from werkzeug.datastructures import FileStorage
import fitz
from flask import current_app
from app.extensions import db
from app.models import ResumeProfile
from app.services.gemini_service import analyze_resume

logger = logging.getLogger(__name__)

def validate_pdf(file_storage: FileStorage) -> tuple[bool, str]:
    """Check extension, try opening with fitz, check page count."""
    if not file_storage or not file_storage.filename:
        return False, "No file provided"
        
    if not file_storage.filename.lower().endswith('.pdf'):
        return False, "File must be a PDF"
        
    file_bytes = file_storage.read()
    file_storage.seek(0)
    
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        max_pages = current_app.config.get('MAX_PDF_PAGES', 5)
        if len(doc) > max_pages:
            doc.close()
            return False, f"PDF exceeds maximum page limit of {max_pages}"
        doc.close()
        return True, "Valid PDF"
    except Exception as e:
        logger.error(f"PDF validation failed: {e}")
        return False, "Invalid or corrupted PDF file"

def convert_pdf_to_images(pdf_path: str) -> list[bytes]:
    """Use fitz to render each page to PNG bytes at 200 DPI."""
    images = []
    try:
        doc = fitz.open(pdf_path)
        # 200 DPI zoom factor
        zoom_x = 200 / 72
        zoom_y = 200 / 72
        mat = fitz.Matrix(zoom_x, zoom_y)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)
        doc.close()
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
    return images

def process_resume(file_storage: FileStorage, user_id: int, api_key: str) -> ResumeProfile:
    """Full pipeline to process a resume PDF."""
    is_valid, error_msg = validate_pdf(file_storage)
    if not is_valid:
        raise ValueError(error_msg)
        
    upload_folder = current_app.config.get('UPLOAD_FOLDER', '/tmp')
    os.makedirs(upload_folder, exist_ok=True)
    temp_path = os.path.join(upload_folder, file_storage.filename)
    
    file_storage.save(temp_path)
    
    try:
        # Extract text for raw_extracted_text and analysis
        doc = fitz.open(temp_path)
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
        doc.close()
        
        # Analyze with Gemini using extracted text
        resume_data = analyze_resume(api_key, raw_text)
        
        # Create profile
        profile = ResumeProfile(
            user_id=user_id,
            original_filename=file_storage.filename,
            is_active=True,
            skills=resume_data.get('skills', []),
            education=resume_data.get('education', []),
            experience=resume_data.get('experience', []),
            projects=resume_data.get('projects', []),
            certifications=resume_data.get('certifications', []),
            technologies=resume_data.get('technologies', []),
            strengths=resume_data.get('strengths', []),
            career_level=resume_data.get('career_level', 'Unknown'),
            summary=resume_data.get('summary', ''),
            raw_extracted_text=raw_text
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return profile
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to remove temp file {temp_path}: {e}")
