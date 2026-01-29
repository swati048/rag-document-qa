from typing import List, Dict, Any
# Modern partner packages
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
# Community and Core
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
# Chain construction - Use langchain_classic for chains in LangChain 1.0+
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
import config

class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        self.vectorstore = None
        self.rag_chain = None
        self.llm = ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.1
        )
        
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
        except Exception as e:
            print(f"No existing vectorstore found or error loading: {e}")
    
    def index_documents(self, documents: List[Document]):
        """Create or update vector store with documents"""
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vectorstore.add_documents(documents)
        
        # Save vectorstore
        index_path = str(config.VECTORSTORE_DIR / "faiss_index")
        self.vectorstore.save_local(index_path)
        
        # Initialize RAG chain
        self._initialize_rag_chain()
    
    def _initialize_rag_chain(self):
        """Initialize the RAG chain with custom prompt"""
        system_prompt = """You are a helpful AI assistant answering questions based on provided documents.

Use ONLY the following context to answer the question. If the answer is not in the context, say "I cannot find this information in the provided documents."

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
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system"""
        if self.rag_chain is None:
            return {
                "answer": "No documents indexed yet. Please upload a document first.",
                "sources": []
            }
        
        try:
            result = self.rag_chain.invoke({"input": question})
            
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
            return {
                "answer": f"Error processing query: {str(e)}",
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