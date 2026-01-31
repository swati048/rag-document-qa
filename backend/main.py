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
    return {"message": "RAG Document Q&A API is running", "llm_provider": "Groq"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        print(f"[UPLOAD] Starting upload: {file.filename}")
        
        # Save file
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        print(f"[UPLOAD] File size: {file_size_mb:.2f} MB")
        
        filepath = doc_manager.save_uploaded_file(content, file.filename)
        print(f"[UPLOAD] File saved to: {filepath}")
        
        # Load and chunk document
        print(f"[UPLOAD] Starting document chunking...")
        documents = doc_manager.load_document(filepath)
        print(f"[UPLOAD] Created {len(documents)} chunks")
        
        # Index documents
        print(f"[UPLOAD] Starting indexing...")
        rag_engine.index_documents(documents)
        print(f"[UPLOAD] Indexing complete")
        
        return {
            "message": f"Successfully uploaded and indexed {file.filename}",
            "chunks": len(documents),
            "file_size_mb": round(file_size_mb, 2)
        }
    except Exception as e:
        print(f"[UPLOAD] Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
    """Check system health"""
    # Check if API key is configured
    api_key_status = "configured" if config.GROQ_API_KEY else "missing"
    
    return {
        "status": "healthy",
        "llm_provider": "Groq",
        "model": config.GROQ_MODEL,
        "api_key_status": api_key_status,
        "documents_indexed": len(doc_manager.list_documents())
    }

if __name__ == "__main__":
    print(f"Starting RAG API with Groq ({config.GROQ_MODEL})")
    print(f"Maximum upload size: 100MB (configurable)")
    # Increased timeout for large file processing
    uvicorn.run(
        app, 
        host=config.API_HOST, 
        port=config.API_PORT,
        timeout_keep_alive=300  # 5 minutes
    )