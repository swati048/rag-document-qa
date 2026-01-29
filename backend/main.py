from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

from document_manager import DocumentManager
from rag_engine import RAGEngine
import config

app = FastAPI(title="RAG Document Q&A API")

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
doc_manager = DocumentManager()
rag_engine = RAGEngine()

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.get("/")
def root():
    return {"message": "RAG Document Q&A API is running"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        # Save file
        content = await file.read()
        filepath = doc_manager.save_uploaded_file(content, file.filename)
        
        # Load and chunk document
        documents = doc_manager.load_document(filepath)
        
        # Index documents
        rag_engine.index_documents(documents)
        
        return {
            "message": f"Successfully uploaded and indexed {file.filename}",
            "chunks": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
def list_documents():
    """List all uploaded documents"""
    return {"documents": doc_manager.list_documents()}

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    """Delete a specific document"""
    success = doc_manager.delete_document(filename)
    if success:
        return {"message": f"Deleted {filename}"}
    raise HTTPException(status_code=404, detail="Document not found")

@app.delete("/documents")
def clear_all_documents():
    """Clear all documents and vector store"""
    doc_manager.clear_all_documents()
    rag_engine.clear_index()
    return {"message": "All documents cleared"}

@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """Query the indexed documents"""
    result = rag_engine.query(request.question)
    return result

@app.get("/health")
def health_check():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=2)
        ollama_status = "running" if response.status_code == 200 else "error"
    except:
        ollama_status = "not running"
    
    return {
        "status": "healthy",
        "ollama": ollama_status,
        "documents_indexed": len(doc_manager.list_documents())
    }

if __name__ == "__main__":
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)