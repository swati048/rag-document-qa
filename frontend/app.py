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

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
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
        if health["ollama"] == "running":
            st.success("✅ System Ready")
        else:
            st.warning("⚠️ Ollama is not responding")
    except Exception as e:
        st.error(f"❌ Backend not reachable")
        st.caption(f"Debug info: {e}")
    
    st.divider()
    
    # Upload section
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file",
        type=['pdf', 'txt'],
        help="Max 20 pages recommended"
    )
    
    if uploaded_file:
        if st.button("📤 Upload & Index", use_container_width=True):
            with st.spinner("Processing document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(f"{API_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Indexed {result['chunks']} chunks")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Upload failed')}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
    
    st.divider()
    
    # Documents list
    st.subheader("Current Documents")
    try:
        docs_response = requests.get(f"{API_URL}/documents")
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

# Main area - Q&A Interface
st.title("🤖 RAG Document Q&A System")
st.markdown("Ask questions about your uploaded documents")

# Display chat history
for i, chat in enumerate(st.session_state.chat_history):
    # User message
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>You:</strong> {chat['question']}
    </div>
    """, unsafe_allow_html=True)
    
    # Assistant message
    st.markdown(f"""
    <div class="chat-message assistant-message">
        <strong>Assistant:</strong> {chat['answer']}
    </div>
    """, unsafe_allow_html=True)
    
    # Sources
    if chat.get('sources'):
        with st.expander(f"📎 View Sources ({len(chat['sources'])} chunks)"):
            for j, source in enumerate(chat['sources'], 1):
                st.markdown(f"""
                <div class="source-box">
                    <strong>Source {j}:</strong> {source['source']} (Chunk {source['chunk']})<br>
                    <small>{source['content']}</small>
                </div>
                """, unsafe_allow_html=True)

# Query input
with st.form(key="query_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "Ask a question:",
            placeholder="What is the main topic of the document?",
            label_visibility="collapsed"
        )
    with col2:
        submit = st.form_submit_button("Ask 🚀", use_container_width=True)

if submit and question:
    with st.spinner("Thinking..."):
        try:
            response = requests.post(
                f"{API_URL}/query",
                json={"question": question},
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": result["answer"],
                    "sources": result.get("sources", []),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                st.rerun()
            else:
                st.error("Query failed")
        except requests.exceptions.Timeout:
            st.error("Request timed out. Ollama might be slow or not responding.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.caption("💡 Tip: Upload a document first, then ask questions about it!")