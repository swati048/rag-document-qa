from typing import List, Dict, Any
import time
# Modern partner packages
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq  # CHANGED: Using Groq instead of Ollama
# Community and Core
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
# Chain construction
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
import config

class RAGEngine:
    def __init__(self):
        # Initialize embeddings (runs locally - no API cost)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
        self.rag_chain = None
        
        # Initialize Groq LLM (cloud-based)
        self.llm = ChatGroq(
            model=config.GROQ_MODEL,
            groq_api_key=config.GROQ_API_KEY,
            temperature=config.GROQ_TEMPERATURE,
            max_retries=2,  # Retry on failure
        )
        
        print(f"[RAG] Initialized with Groq model: {config.GROQ_MODEL}")
        
        # Load existing vectorstore if available
        self._load_vectorstore()
    
    def _load_vectorstore(self):
        """Load existing FAISS vectorstore if available"""
        try:
            index_path = str(config.VECTORSTORE_DIR / "faiss_index")
            if (config.VECTORSTORE_DIR / "faiss_index").exists():
                self.vectorstore = FAISS.load_local(
                    index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                self._initialize_rag_chain()
                print("[RAG] Loaded existing vectorstore")
        except Exception as e:
            print(f"[RAG] No existing vectorstore found or error loading: {e}")
    
    def index_documents(self, documents: List[Document]):
        """Create or update vector store with documents"""
        print(f"[RAG] Indexing {len(documents)} document chunks...")
        
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vectorstore.add_documents(documents)
        
        # Save vectorstore
        index_path = str(config.VECTORSTORE_DIR / "faiss_index")
        self.vectorstore.save_local(index_path)
        
        # Initialize RAG chain
        self._initialize_rag_chain()
        print("[RAG] Documents indexed successfully")
    
    def _initialize_rag_chain(self):
        """Initialize the RAG chain with custom prompt"""
        system_prompt = """You are a helpful AI assistant answering questions based on provided documents.

Use ONLY the following context to answer the question. If the answer is not in the context, say "I cannot find this information in the provided documents."

Be concise and accurate. Cite specific parts of the context when possible.

Context: {context}"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        # Create the combine documents chain
        combine_docs_chain = create_stuff_documents_chain(self.llm, prompt)
        
        # Create the retrieval chain
        self.rag_chain = create_retrieval_chain(
            self.vectorstore.as_retriever(search_kwargs={"k": config.TOP_K_RESULTS}),
            combine_docs_chain
        )
        print("[RAG] RAG chain initialized")
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        if self.rag_chain is None:
            return {
                "answer": "No documents indexed yet. Please upload a document first.",
                "sources": []
            }
        
        try:
            print(f"[RAG] Processing query: {question}")
            start_time = time.time()
            
            # Invoke the RAG chain
            result = self.rag_chain.invoke({"input": question})
            
            elapsed = time.time() - start_time
            print(f"[RAG] Response received in {elapsed:.2f}s")
            
            # Format sources
            sources = []
            for doc in result.get("context", []):
                sources.append({
                    "content": doc.page_content[:200] + "...",  # Preview
                    "source": doc.metadata.get("source", "Unknown"),
                    "chunk": doc.metadata.get("chunk", 0)
                })
            
            return {
                "answer": result["answer"],
                "sources": sources
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[RAG] Error: {error_msg}")
            
            # Handle specific Groq errors
            if "rate_limit" in error_msg.lower():
                return {
                    "answer": "Rate limit exceeded. Please wait a moment and try again. (Groq free tier: 30 requests/min)",
                    "sources": []
                }
            elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return {
                    "answer": "API authentication error. Please check your GROQ_API_KEY in the .env file.",
                    "sources": []
                }
            else:
                return {
                    "answer": f"Error processing query: {error_msg}",
                    "sources": []
                }
    
    def clear_index(self):
        """Clear the vector store"""
        self.vectorstore = None
        self.rag_chain = None
        
        # Delete saved index
        index_path = config.VECTORSTORE_DIR / "faiss_index"
        if index_path.exists():
            import shutil
            shutil.rmtree(config.VECTORSTORE_DIR)
            config.VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
        print("[RAG] Vector store cleared")