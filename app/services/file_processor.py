# app/services/file_processor.py

import io
from fastapi import HTTPException, status
import PyPDF2
import docx

async def extract_text(content: bytes, filename: str) -> str:
    file_stream = io.BytesIO(content)
    
    if filename.endswith('.pdf'):
        try:
            reader = PyPDF2.PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing PDF file: {e}"
            )
    
    elif filename.endswith('.docx'):
        try:
            document = docx.Document(file_stream)
            text = "\n".join([para.text for para in document.paragraphs])
            return text
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing DOCX file: {e}"
            )
            
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload a .pdf or .docx file."
        )