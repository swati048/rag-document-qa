from typing import List, Dict, Any, Optional
import time
import re
# Modern partner packages
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
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
            max_retries=2,
        )
        
        print(f"[RAG] Initialized with Groq model: {config.GROQ_MODEL}")
        print(f"[RAG] Settings: CHUNK_SIZE={config.CHUNK_SIZE}, TOP_K={config.TOP_K_RESULTS}")
        
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
    
    def delete_document_from_vectorstore(self, filename: str) -> bool:
        """
        Delete all chunks belonging to a specific file from the vector store
        FAISS doesn't support direct deletion, so we rebuild the index
        """
        if self.vectorstore is None:
            print(f"[RAG] No vectorstore exists, nothing to delete")
            return False
        
        try:
            print(f"[RAG] Deleting chunks for: {filename}")
            
            # Get all documents from the vectorstore
            # We need to rebuild without the deleted file's chunks
            all_docs = self.vectorstore.docstore._dict
            
            # Filter out documents from the deleted file
            remaining_docs = []
            deleted_count = 0
            
            for doc_id, doc in all_docs.items():
                if doc.metadata.get("filename") != filename:
                    remaining_docs.append(doc)
                else:
                    deleted_count += 1
            
            print(f"[RAG] Found {deleted_count} chunks to delete")
            
            if len(remaining_docs) == 0:
                # No documents left, clear the vectorstore
                print(f"[RAG] No documents remaining, clearing vectorstore")
                self.clear_index()
                return True
            
            # Rebuild vectorstore with remaining documents
            print(f"[RAG] Rebuilding vectorstore with {len(remaining_docs)} remaining chunks")
            self.vectorstore = FAISS.from_documents(remaining_docs, self.embeddings)
            
            # Save the updated vectorstore
            index_path = str(config.VECTORSTORE_DIR / "faiss_index")
            self.vectorstore.save_local(index_path)
            
            # Reinitialize RAG chain
            self._initialize_rag_chain()
            
            print(f"[RAG] Successfully deleted {deleted_count} chunks from {filename}")
            return True
            
        except Exception as e:
            print(f"[RAG] Error deleting document from vectorstore: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_filename_from_query(self, query: str) -> Optional[str]:
        """
        Extract filename from query if user mentions a specific file
        Examples:
        - "What is in story.txt?"
        - "Summarize document.pdf"
        - "What does the report.txt say?"
        """
        # Pattern to match common file extensions
        pattern = r'\b(\w+\.(txt|pdf))\b'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if match:
            filename = match.group(1)
            print(f"[RAG] Detected filename in query: {filename}")
            return filename
        
        return None
    
    def _reformulate_query_for_search(self, query: str, filename: Optional[str]) -> str:
        """
        Reformulate generic queries into more specific ones for better semantic search
        """
        search_query = query

        # Strip filename once at the start
        if filename:
            search_query = re.sub(r'\b\w+\.(txt|pdf)\b', '', query, flags=re.IGNORECASE).strip()
        
        # Generic query patterns that need reformulation
        generic_patterns = {
            r'summarize|summarise|summary': 'summary of main topics and key points',
            r'what is in|what\'s in|content of': 'comprehensive overview of content',
            r'tell me about': 'explain',
            r'overview of': 'main information about',
        }
        
        # Check if query is generic
        for pattern, replacement in generic_patterns.items():
            if re.search(pattern, search_query.lower()):
                final_query = f"{search_query}, {replacement}".strip()
                print(f"[RAG] Reformulated query: '{search_query}' -> '{final_query}'")
                return final_query
                    
        return search_query
    
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
        
        # Create the retrieval chain with base retriever (no filtering yet)
        base_retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": config.TOP_K_RESULTS}
        )
        
        self.rag_chain = create_retrieval_chain(
            base_retriever,
            combine_docs_chain
        )
        print("[RAG] RAG chain initialized")

    def _get_filtered_documents(self, query: str, filename: str) -> List[Document]:
        """Get documents filtered by filename using native FAISS filtering"""
        return self.vectorstore.similarity_search(
            query, 
            k=config.TOP_K_RESULTS, 
            filter={'filename': filename},
            fetch_k=200  # Deep dive to ensure we find chunks from this specific file
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system with optional filename filtering"""
        if self.vectorstore is None:
            return {
                "answer": "No documents indexed yet. Please upload a document first.",
                "sources": [],
                "filtered_by": None
            }
        
        try:
            print(f"[RAG] Processing query: {question}")
            
            # Check if user mentioned a specific file
            target_filename = self._extract_filename_from_query(question)
            
            if target_filename:
                # Reformulate query for better semantic search
                search_query = self._reformulate_query_for_search(question, target_filename)
                
                print(f"[RAG] Filtering search to file: {target_filename}")
                print(f"[RAG] Search query: {search_query}")
                
                # Get filtered documents
                filtered_docs = self._get_filtered_documents(search_query, target_filename)
                num_chunks = len(filtered_docs)

                if num_chunks == 0:
                    print(f"[RAG] No chunks found for {target_filename}")
                    return {
                        "answer": f"No relevant information found in {target_filename}. The file might be empty or the question might not match the content.",
                        "sources": [],
                        "filtered_by": target_filename,
                        "chunks_retrieved": 0
                    }
                
                print(f"[RAG] Found {num_chunks} chunks from {target_filename}")
                
                # Format context for LLM
                context_text = "\n\n".join([doc.page_content for doc in filtered_docs])
                
                # Create prompt
                prompt_text = f"""You are a helpful AI assistant answering questions based on provided documents.

Use ONLY the following context to answer the question. If the answer is not in the context, say "I cannot find this information in the provided documents."

Be concise and accurate. Cite specific parts of the context when possible.

Context: {context_text}

Question: {search_query}"""
                
                # Query LLM directly
                start_time = time.time()
                response = self.llm.invoke(prompt_text)
                elapsed = time.time() - start_time
                
                answer = response.content if hasattr(response, 'content') else str(response)
                
                print(f"[RAG] Response received in {elapsed:.2f}s (filtered by {target_filename})")
                
                # Format sources
                sources = []
                for doc in filtered_docs:
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "source": doc.metadata.get("source", "Unknown"),
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "chunk": doc.metadata.get("chunk", 0),
                        "file_type": doc.metadata.get("file_type", "unknown")
                    })
                
                return {
                    "answer": answer,
                    "sources": sources,
                    "filtered_by": target_filename,
                    "chunks_retrieved": len(sources)
                }
            else:
                # Use normal retrieval across all documents
                start_time = time.time()
                result = self.rag_chain.invoke({"input": question})
                elapsed = time.time() - start_time
                print(f"[RAG] Response received in {elapsed:.2f}s (no filtering)")
                
                # Format sources with metadata
                sources = []
                for doc in result.get("context", []):
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "source": doc.metadata.get("source", "Unknown"),
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "chunk": doc.metadata.get("chunk", 0),
                        "file_type": doc.metadata.get("file_type", "unknown")
                    })
                
                return {
                    "answer": result["answer"],
                    "sources": sources,
                    "filtered_by": None,
                    "chunks_retrieved": len(sources)
                }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[RAG] Error: {error_msg}")
            
            # Handle specific Groq errors
            if "rate_limit" in error_msg.lower():
                return {
                    "answer": "Rate limit exceeded. Please wait a moment and try again. (Groq free tier: 30 requests/min)",
                    "sources": [],
                    "filtered_by": None
                }
            elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                return {
                    "answer": "API authentication error. Please check your GROQ_API_KEY in the .env file.",
                    "sources": [],
                    "filtered_by": None
                }
            else:
                return {
                    "answer": f"Error processing query: {error_msg}",
                    "sources": [],
                    "filtered_by": None
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