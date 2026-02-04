import streamlit as st
import requests
import json
from pathlib import Path
from datetime import datetime

# Backend API URL
API_URL = "http://localhost:8000"

# --- Chat Persistence (survives refresh) ---
CHAT_HISTORY_PATH = Path(__file__).parent.parent / "data" / "chat_history.json"
CHAT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_chat_history() -> list:
    """Load chat history from disk. Returns empty list if file missing or corrupt."""
    try:
        if CHAT_HISTORY_PATH.exists():
            with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return []

def save_chat_history(history: list):
    """Write current chat history to disk."""
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def clear_chat_history():
    """Delete the chat history file from disk."""
    if CHAT_HISTORY_PATH.exists():
        CHAT_HISTORY_PATH.unlink()

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
    .filter-badge {
        display: inline-block;
        background-color: rgba(255, 152, 0, 0.2);
        border: 1px solid rgba(255, 152, 0, 0.5);
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        margin-left: 0.5rem;
    }
    .timestamp {
        font-size: 0.72rem;
        opacity: 0.45;
        margin-top: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state — load persisted chat on first run only
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = load_chat_history()
if 'deleting_file' not in st.session_state:
    st.session_state.deleting_file = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
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
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.caption(f"📦 File size: {file_size_mb:.2f} MB")

        if st.button("📤 Upload & Index", use_container_width=True):
            estimated_time = max(60, int(file_size_mb * 30))

            with st.spinner(f"Processing document... (may take up to {estimated_time}s for large files)"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(
                        f"{API_URL}/upload",
                        files=files,
                        timeout=300
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

    # Handle deletion if triggered
    if st.session_state.deleting_file:
        with st.spinner(f"Deleting {st.session_state.deleting_file}..."):
            try:
                delete_response = requests.delete(
                    f"{API_URL}/documents/{st.session_state.deleting_file}",
                    timeout=300
                )

                st.session_state.deleting_file = None

                if delete_response.status_code == 200:
                    st.rerun()
                else:
                    st.error(f"Failed to delete: {delete_response.text}")

            except requests.exceptions.Timeout:
                st.session_state.deleting_file = None
                st.error("Delete request timed out. File may still be deleted - refresh the page.")
            except Exception as e:
                st.session_state.deleting_file = None
                st.error(f"Delete error: {str(e)}")

    # Display documents list
    try:
        docs_response = requests.get(f"{API_URL}/documents", timeout=5)
        documents = docs_response.json()["documents"]

        if documents:
            for doc in documents:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {doc['filename']}")
                    st.caption(f"{doc['size']} • {doc['uploaded']}")
                with col2:
                    if st.button("🗑️", key=f"delete_{doc['filename']}", help="Delete"):
                        st.session_state.deleting_file = doc['filename']
                        st.rerun()
        else:
            st.info("No documents uploaded yet")
    except Exception as e:
        st.error(f"Cannot load documents: {str(e)}")

    st.divider()

    # Clear all documents (does NOT touch chat)
    if st.button("🗑️ Clear All Documents", use_container_width=True, type="secondary"):
        with st.spinner("Clearing all documents..."):
            try:
                response = requests.delete(f"{API_URL}/documents", timeout=300)
                if response.status_code == 200:
                    st.rerun()
                else:
                    st.error("Failed to clear documents")
            except Exception as e:
                st.error(f"Clear failed: {str(e)}")

    # Clear chat — only shown when there is actually something to clear,
    # and styled as primary so it's visually distinct from "Clear All Documents"
    if st.session_state.chat_history:
        if st.button("🧹 Clear Chat", use_container_width=True, type="primary"):
            with st.spinner("Clearing chat history..."):
                st.session_state.chat_history = []
                clear_chat_history()
                st.rerun()

    st.divider()

    # Usage info
    with st.expander("ℹ️ About This System"):
        st.markdown("""
        **Powered by:**
        - 🤖 Groq (Cloud LLM - Free Tier)
        - 🔍 FAISS (Vector Search)
        - 🧠 HuggingFace Embeddings (Local)

        **Settings:**
        - Chunk size: 1500 chars
        - Top K results: 9 chunks
        - Model: Llama 3.3 70B

        **File Filtering:**
        Mention a filename in your question!
        - "What is in doc.txt?"
        - "Summarize report.pdf"
        """)

# ---------------------------------------------------------------------------
# Main area — Q&A
# ---------------------------------------------------------------------------
st.title("🤖 RAG Document Q&A System")
st.markdown("Ask questions about your uploaded documents • Powered by Groq")

# Chat history display
if st.session_state.chat_history:
    for i, chat in enumerate(st.session_state.chat_history):
        # User message (with timestamp)
        with st.container():
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {chat.get('question', 'No question')}
                <div class="timestamp">🕐 {chat.get('timestamp', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Assistant message
        with st.container():
            answer = chat.get('answer', 'No answer received')
            filtered_by = chat.get('filtered_by')
            chunks_retrieved = chat.get('chunks_retrieved', 0)
            
            filter_badge = f'\n<div class="filter-badge">🎯 Filtered by: {filtered_by}</div>' if filtered_by else ''

            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong> <small>({chunks_retrieved} chunks)</small><br>
                {answer}{filter_badge}
            </div>
            """, unsafe_allow_html=True)

        # Sources
        sources = chat.get('sources', [])
        if sources and len(sources) > 0:
            with st.expander(f"🔎 View Sources ({len(sources)} chunks)", expanded=False):
                for j, source in enumerate(sources, 1):
                    filename = source.get('filename', source.get('source', 'Unknown'))
                    file_type = source.get('file_type', 'unknown')
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Source {j}:</strong> {filename} ({file_type.upper()}) - Chunk {source.get('chunk', 0)}<br>
                        <small>{source.get('content', 'No content')}</small>
                    </div>
                    """, unsafe_allow_html=True)

else:
    # Context-aware empty state: different message depending on whether
    # documents are already loaded or not
    try:
        _doc_count = len(requests.get(f"{API_URL}/documents", timeout=3).json()["documents"])
    except Exception:
        _doc_count = 0

    if _doc_count == 0:
        st.info("👋 Welcome! Upload a document in the sidebar, then start asking questions.")
        st.markdown("""
        **💡 Pro Tips:**
        - Upload multiple documents
        - Ask: *"What is in doc.txt?"* to search only that file
        - Ask: *"Compare the two documents"* to search across all files
        - Provide clear context in your questions for better responses
        """)
    else:
        st.info(f"👋 You have {_doc_count} document(s) loaded — ask your first question below!")

# Query input
st.markdown("---")
with st.form(key="query_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "Ask a question:",
            placeholder="What is the main topic? (or: Summarize doc.txt?)",
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

                st.session_state.chat_history.append({
                    "question": question,
                    "answer": result.get("answer", "No answer received"),
                    "sources": result.get("sources", []),
                    "filtered_by": result.get("filtered_by"),
                    "chunks_retrieved": result.get("chunks_retrieved", 0),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                save_chat_history(st.session_state.chat_history)

                st.rerun()
            else:
                st.error(f"Query failed with status {response.status_code}")

        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to backend. Make sure it's running.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ---------------------------------------------------------------------------
# Footer — context-aware tip
# ---------------------------------------------------------------------------
st.divider()
col1, col2 = st.columns(2)
with col1:
    # Reuse _doc_count if it was set above; otherwise fetch it now
    try:
        _footer_docs = len(requests.get(f"{API_URL}/documents", timeout=2).json()["documents"])
    except Exception:
        _footer_docs = 0

    if _footer_docs > 0:
        st.caption("💡 Tip: Mention a filename to filter search (e.g., 'What is in doc.pdf?')")
    else:
        st.caption("💡 Tip: Upload a document in the sidebar to get started.")
with col2:
    st.caption("⚡ Powered by Groq's free tier (30 requests/min)")