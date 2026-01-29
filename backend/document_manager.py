import os
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import config

class DocumentManager:
    def __init__(self):
        self.upload_dir = config.UPLOAD_DIR
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
        )
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file and return filepath"""
        filepath = self.upload_dir / filename
        with open(filepath, "wb") as f:
            f.write(file_content)
        return str(filepath)
    
    def load_document(self, filepath: str) -> List[Document]:
        """Load and chunk document"""
        file_ext = Path(filepath).suffix.lower()
        
        if file_ext == ".pdf":
            text = self._extract_pdf_text(filepath)
        elif file_ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create Document objects with metadata
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "source": Path(filepath).name,
                    "chunk": i,
                    "total_chunks": len(chunks)
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        return documents
    
    def _extract_pdf_text(self, filepath: str) -> str:
        """Extract text from PDF"""
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def list_documents(self) -> List[Dict[str, str]]:
        """List all uploaded documents"""
        docs = []
        for file in self.upload_dir.iterdir():
            if file.is_file() and file.suffix in [".pdf", ".txt"]:
                stats = file.stat()
                docs.append({
                    "filename": file.name,
                    "size": f"{stats.st_size / 1024:.2f} KB",
                    "uploaded": datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M"),
                })
        return docs
    
    def delete_document(self, filename: str) -> bool:
        """Delete a document"""
        filepath = self.upload_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def clear_all_documents(self):
        """Delete all documents and vector store"""
        # Clear uploads
        for file in self.upload_dir.iterdir():
            if file.is_file():
                file.unlink()
        
        # Clear vector store
        if config.VECTORSTORE_DIR.exists():
            shutil.rmtree(config.VECTORSTORE_DIR)
            config.VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)