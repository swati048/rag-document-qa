# 📚 RAG Document Q&A System

A local, free AI-powered document question-answering system using Retrieval Augmented Generation (RAG). Upload PDFs or text files and ask questions in natural language!

## 🎯 Features

- ✅ **100% Free & Local** - Uses Ollama (llama3.2:3b) and open-source models
- ✅ **Persistent Storage** - Documents and embeddings saved between sessions
- ✅ **Document Management** - Upload, view, and delete documents
- ✅ **Source Citations** - See which document chunks support each answer
- ✅ **Chat History** - Track your conversation within a session
- ✅ **Fast Responses** - Optimized for 10-20 page documents

## 🛠️ Tech Stack

- **Backend:** FastAPI + LangChain + FAISS
- **LLM:** Ollama (llama3.2:3b)
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Frontend:** Streamlit
- **Storage:** Local filesystem

## 📋 Prerequisites

1. **Python 3.9+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)

## 🚀 Installation

### Step 1: Install Ollama

```bash
# For Mac/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# For Windows
# Download from https://ollama.ai/download
```

### Step 2: Pull the LLM Model

```bash
# Pull the 3B model (default, ~2GB)
ollama pull llama3.2

# OR for the smaller/faster 1B model
ollama pull llama3.2:1b
```

### Step 3: Clone & Setup Project

```bash
# Create project directory
mkdir rag-document-qa
cd rag-document-qa

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Create Project Structure

```
rag-document-qa/
├── backend/
│   ├── __init__.py          (create empty file)
│   ├── config.py
│   ├── document_manager.py
│   ├── rag_engine.py
│   └── main.py
├── frontend/
│   └── app.py
├── data/
│   ├── uploads/             (auto-created)
│   └── vectorstore/         (auto-created)
├── requirements.txt
└── README.md
```

## ▶️ Running the Application

### Terminal 1: Start Ollama (if not auto-running)

```bash
ollama serve
```

### Terminal 2: Start Backend

```bash
cd backend
python main.py
```

**Backend will run at:** http://localhost:8000

### Terminal 3: Start Frontend

```bash
cd frontend
streamlit run app.py
```

**Frontend will open at:** http://localhost:8501

## 📖 Usage Guide

1. **Upload a Document**
   - Click "Choose a PDF or TXT file" in the sidebar
   - Select your document (10-20 pages recommended)
   - Click "Upload & Index"
   - Wait for chunking and embedding (may take 30-60 seconds)

2. **Ask Questions**
   - Type your question in the input box
   - Click "Ask 🚀"
   - Get AI-generated answers based on your document
   - View source citations by expanding the "View Sources" section

3. **Manage Documents**
   - See all uploaded documents in the sidebar
   - Delete individual documents with 🗑️ button
   - Clear all documents with "Clear All Documents" button

## 🎨 Example Questions

- "What is the main topic of this document?"
- "Summarize the key findings in section 3"
- "What are the recommendations mentioned?"
- "Who are the authors and what are their affiliations?"

## ⚙️ Configuration

Edit `backend/config.py` to customize:

```python
# LLM Model options:
# - "llama3.2" (default 3B, ~2GB, good speed/quality balance)
# - "llama3.2:1b" (1B, ~1GB, faster but less capable)
OLLAMA_MODEL = "llama3.2"

# Chunk size for document splitting
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Number of relevant chunks to retrieve
TOP_K_RESULTS = 4
```

## 🔧 Troubleshooting

### "Ollama not running"
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve
```

### "Backend not reachable"
```bash
# Check if backend is running on port 8000
curl http://localhost:8000/health
```

### Slow responses
- Use smaller model: `ollama pull llama3.2:1b`
- Reduce `TOP_K_RESULTS` in config
- Use shorter documents (<10 pages)

### Out of memory
- Close other applications
- Use `llama3.2:1b` instead of `3b`
- Reduce `CHUNK_SIZE` to 500

## 📁 Project Structure Explained

```
backend/
├── config.py              # Configuration settings
├── document_manager.py    # Upload/delete/list documents
├── rag_engine.py          # Core RAG logic (embeddings, retrieval, LLM)
└── main.py                # FastAPI endpoints

frontend/
└── app.py                 # Streamlit UI

data/
├── uploads/               # Stored PDF/TXT files
└── vectorstore/           # FAISS index (embeddings)
```

## 🚀 Performance Tips

1. **First query is slower** - Embeddings model loads into memory
2. **Subsequent queries are faster** - Model stays in memory
3. **Optimal doc size** - 10-20 pages for best speed/quality balance
4. **Restart Ollama** if responses become slow over time

## 🤝 Contributing

This is a portfolio project, but suggestions welcome! Open an issue or PR.

## 📄 License

MIT License - feel free to use for your own projects!

## 🙏 Acknowledgments

- [LangChain](https://langchain.com) - RAG framework
- [Ollama](https://ollama.ai) - Local LLM runtime
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [Streamlit](https://streamlit.io) - Frontend framework

---

**Made with ❤️ for GitHub Portfolio**

Star ⭐ this repo if you found it helpful!