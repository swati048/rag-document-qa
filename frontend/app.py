import streamlit as st
import requests
from datetime import datetime

# Backend API URL
API_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="RAG Document Q&A",
    page_icon="📚",
    layout="wide"
)

# Custom CSS - Dark mode compatible
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .source-box {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
        color: inherit;
    }
    .user-message {
        background-color: rgba(31, 119, 180, 0.1);
        border-left-color: #1976d2;
    }
    .assistant-message {
        background-color: rgba(67, 160, 71, 0.1);
        border-left-color: #43a047;
    }
    .chat-message strong {
        color: inherit;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar - Document Management
with st.sidebar:
    st.title("📚 Document Manager")
    
    # Health check
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        health = health_response.json()
        
        if health.get("status") == "healthy":
            st.success("✅ System Ready")
            st.caption(f"🤖 Using Groq (Cloud LLM)")
            st.caption(f"📊 Model: {health.get('model', 'Unknown')}")
            if health.get("documents_indexed", 0) > 0:
                st.info(f"📄 {health['documents_indexed']} documents indexed")
        else:
            st.error("❌ System Error")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Backend not running")
        st.caption("Run: `cd backend && python main.py`")
    except Exception as e:
        st.error(f"❌ Connection Error")
        st.caption(f"Error: {str(e)}")
    
    st.divider()
    
    # Upload section
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file",
        type=['pdf', 'txt'],
        help="Large files may take 1-3 minutes to process"
    )
    
    if uploaded_file:
        # Show file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.caption(f"📦 File size: {file_size_mb:.2f} MB")
        
        if st.button("📤 Upload & Index", use_container_width=True):
            # Estimate processing time based on file size
            estimated_time = max(60, int(file_size_mb * 30))  # ~30 seconds per MB
            
            with st.spinner(f"Processing document... (may take up to {estimated_time}s for large files)"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    # INCREASED TIMEOUT: 5 minutes for large files
                    response = requests.post(
                        f"{API_URL}/upload", 
                        files=files, 
                        timeout=300  # 5 minutes
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Indexed {result['chunks']} chunks")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Upload failed')}")
                except requests.exceptions.Timeout:
                    st.warning("⏱️ Upload is taking longer than expected. Check backend logs - the file might still be processing.")
                    st.info("💡 Tip: Refresh the page in 1 minute to see if the document appears in the list.")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
    
    st.divider()
    
    # Documents list
    st.subheader("Current Documents")
    try:
        docs_response = requests.get(f"{API_URL}/documents", timeout=5)
        documents = docs_response.json()["documents"]
        
        if documents:
            for doc in documents:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📄 {doc['filename']}")
                        st.caption(f"{doc['size']} • {doc['uploaded']}")
                    with col2:
                        if st.button("🗑️", key=doc['filename'], help="Delete"):
                            try:
                                requests.delete(f"{API_URL}/documents/{doc['filename']}")
                                st.success("Deleted!")
                                st.rerun()
                            except:
                                st.error("Delete failed")
        else:
            st.info("No documents uploaded yet")
    except:
        st.error("Cannot load documents")
    
    st.divider()
    
    # Clear all
    if st.button("🗑️ Clear All Documents", use_container_width=True, type="secondary"):
        try:
            requests.delete(f"{API_URL}/documents")
            st.session_state.chat_history = []
            st.success("All cleared!")
            st.rerun()
        except:
            st.error("Clear failed")
    
    st.divider()
    
    # Usage info
    with st.expander("ℹ️ About This System"):
        st.markdown("""
        **Powered by:**
        - 🤖 Groq (Cloud LLM - Free Tier)
        - 🔍 FAISS (Vector Search)
        - 🧠 HuggingFace Embeddings (Local)
        
        **Free Tier Limits:**
        - 30 questions/minute
        - Unlimited documents
        
        **Model:** Llama 3.3 70B
        
        **File Size Tips:**
        - Small files (<5MB): ~30 seconds
        - Medium files (5-20MB): 1-2 minutes
        - Large files (>20MB): 2-5 minutes
        """)

# Main area - Q&A Interface
st.title("🤖 RAG Document Q&A System")
st.markdown("Ask questions about your uploaded documents • Powered by Groq")

# Display chat history
if st.session_state.chat_history:
    for i, chat in enumerate(st.session_state.chat_history):
        # User message
        with st.container():
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {chat.get('question', 'No question')}
            </div>
            """, unsafe_allow_html=True)
        
        # Assistant message
        with st.container():
            answer = chat.get('answer', 'No answer received')
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>
                {answer}
            </div>
            """, unsafe_allow_html=True)
        
        # Sources
        sources = chat.get('sources', [])
        if sources and len(sources) > 0:
            with st.expander(f"🔎 View Sources ({len(sources)} chunks)", expanded=False):
                for j, source in enumerate(sources, 1):
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Source {j}:</strong> {source.get('source', 'Unknown')} (Chunk {source.get('chunk', 0)})<br>
                        <small>{source.get('content', 'No content')}</small>
                    </div>
                    """, unsafe_allow_html=True)
else:
    st.info("👋 Welcome! Upload a document and start asking questions.")

# Query input
st.markdown("---")
with st.form(key="query_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "Ask a question:",
            placeholder="What is the main topic of the document?",
            label_visibility="collapsed",
            key="question_input"
        )
    with col2:
        submit = st.form_submit_button("Ask 🚀", use_container_width=True)

if submit and question:
    with st.spinner("🤔 Thinking... (querying Groq)"):
        try:
            response = requests.post(
                f"{API_URL}/query",
                json={"question": question},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": result.get("answer", "No answer received"),
                    "sources": result.get("sources", []),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                st.rerun()
            else:
                st.error(f"Query failed with status {response.status_code}")
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to backend. Make sure it's running.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption("💡 Tip: Upload a document first, then ask questions about it!")
with col2:
    st.caption("⚡ Powered by Groq's free tier (30 requests/min)")