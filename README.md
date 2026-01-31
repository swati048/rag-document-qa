# 📚 RAG Document Q&A System (Groq Cloud Edition)

A **free, cloud-powered** AI document question-answering system using Retrieval Augmented Generation (RAG). Upload PDFs or text files and ask questions in natural language!

## ✨ What Changed (Ollama → Groq Migration)

**Before:** Local Ollama LLM (required 4-8GB RAM)  
**After:** Groq Cloud API (FREE tier, no local resources needed)

### Benefits:
- ✅ **No RAM requirements** - LLM runs in the cloud
- ✅ **Faster responses** - Groq's optimized inference
- ✅ **Better quality** - Access to Llama 3.1 70B model
- ✅ **100% FREE** for typical usage (30 requests/min)
- ✅ **No local setup** - Just install Python packages

---

## 🎯 Features

- ✅ **100% Free** - Groq free tier (30 requests/min)
- ✅ **Cloud-powered LLM** - Llama 3.1 70B via Groq
- ✅ **Local Embeddings** - No API costs for document indexing
- ✅ **Persistent Storage** - Documents saved between sessions
- ✅ **Source Citations** - See which chunks support each answer
- ✅ **Chat History** - Track conversations
- ✅ **Fast Setup** - No local LLM installation needed

---

## 🛠️ Tech Stack

- **Backend:** FastAPI + LangChain + FAISS
- **LLM:** Groq (Llama 3.1 70B) - Cloud API
- **Embeddings:** HuggingFace (local, free)
- **Frontend:** Streamlit
- **Storage:** Local filesystem

---

## 📋 Prerequisites

1. **Python 3.9+**
2. **Groq API Key** (free) - Get from [console.groq.com](https://console.groq.com)

---

## 🚀 Quick Start (5 Steps)

### Step 1: Get Your Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Sign up (free) with Google/GitHub/Email
3. Go to "API Keys" → "Create API Key"
4. Copy your key (starts with `gsk_...`)

### Step 2: Clone/Setup Project

```bash
# Create project directory
mkdir rag-groq
cd rag-groq

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### Step 3: Create Project Structure

```
rag-groq/
├── backend/
│   ├── __init__.py          # Create empty file
│   ├── config.py            # Copy from updated files
│   ├── document_manager.py  # Copy from updated files
│   ├── rag_engine.py        # Copy from updated files
│   └── main.py              # Copy from updated files
├── frontend/
│   └── app.py               # Copy from updated files
├── .env                     # YOU CREATE THIS (see Step 4)
├── .gitignore
├── requirements.txt         # Copy from updated files
└── README.md
```

### Step 4: Setup Environment Variables

Create a `.env` file in the **root directory** (same level as `backend/` folder):

```bash
# .env file
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

**IMPORTANT:**
- Replace `gsk_your_actual_groq_api_key_here` with your real API key
- Never commit this file to Git (already in .gitignore)

### Step 5: Install Dependencies & Run

```bash
# Install all packages
pip install -r requirements.txt

# Terminal 1: Start Backend
cd backend
python main.py
# Backend runs at: http://localhost:8000

# Terminal 2: Start Frontend (open new terminal)
cd frontend
streamlit run app.py
# Frontend opens at: http://localhost:8501
```

---

## 💰 Cost & Limits (Groq Free Tier)

**Your Free Tier Includes:**
- ✅ **30 requests per minute**
- ✅ **14,400 tokens per minute**
- ✅ **Unlimited documents** (stored locally)
- ✅ **No credit card required**

**Models Available:**
- `llama-3.1-70b-versatile` ⭐ (default - best quality)
- `llama-3.1-8b-instant` (faster)
- `mixtral-8x7b-32768` (good balance)

**Typical Usage:**
- Document upload: **0 API calls** (embeddings are local)
- Each question: **1 API call**
- **100-200 questions/day = 100% FREE** ✅

---

## 📖 Usage Guide

### 1. Upload Documents

1. Open http://localhost:8501
2. Click "Choose a PDF or TXT file" in sidebar
3. Select your document (10-20 pages recommended)
4. Click "📤 Upload & Index"
5. Wait for indexing (~10-30 seconds)

### 2. Ask Questions

- Type your question in the input box
- Click "Ask 🚀"
- Get AI answers based on your documents
- Expand "🔎 View Sources" to see citations

### 3. Manage Documents

- View all documents in sidebar
- Delete individual documents with 🗑️
- Clear all with "Clear All Documents"

---

## 🎨 Example Questions

```
- "What is the main topic of this document?"
- "Summarize the key findings"
- "What recommendations are mentioned?"
- "Who are the authors?"
- "Compare the results in sections 2 and 3"
```

---

## ⚙️ Configuration

Edit `backend/config.py` to customize:

```python
# Switch models (if needed)
GROQ_MODEL = "llama-3.1-70b-versatile"  # Best quality
# GROQ_MODEL = "llama-3.1-8b-instant"   # Faster

# Chunk size for documents
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Number of relevant chunks to retrieve
TOP_K_RESULTS = 4
```

---

## 🔧 Troubleshooting

### "GROQ_API_KEY not found"
```bash
# Check if .env file exists in root directory
ls -la .env

# Make sure it contains:
GROQ_API_KEY=gsk_your_key_here
```

### "Backend not reachable"
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return JSON with status
```

### "Rate limit exceeded"
- You've hit 30 requests/minute
- Wait 60 seconds and try again
- Consider using `llama-3.1-8b-instant` for faster queries

### Slow responses
- First query may take 5-10 seconds (normal)
- Subsequent queries should be 1-3 seconds
- Switch to `llama-3.1-8b-instant` for speed

---

## 📊 Performance Comparison

| Metric | Ollama (Local) | Groq (Cloud) |
|--------|----------------|--------------|
| Setup | Complex | Simple |
| RAM needed | 4-8GB | 0GB |
| First query | 30-60s | 5-10s |
| Subsequent | 10-20s | 1-3s |
| Model quality | 1B-3B | 70B |
| Cost | Free | Free tier |

---

## 🚀 Deployment Tips

### For Production:
1. **Secure your API key** - Use proper environment management
2. **Add rate limiting** - Implement backend throttling
3. **Monitor usage** - Track API calls in Groq dashboard
4. **Add authentication** - Protect your Streamlit app
5. **Use HTTPS** - Secure API communications

### Upgrade Options:
- **Groq Pro** - Higher rate limits if needed
- **Add caching** - Store common queries
- **Multiple models** - Let users choose speed vs quality

---

## 🆚 Groq vs Other Providers

| Provider | Free Tier | Speed | Setup |
|----------|-----------|-------|-------|
| **Groq** ⭐ | 30 req/min | Very Fast | Easy |
| OpenAI | $5 credit | Fast | Easy |
| Google AI | 60 req/min | Fast | Easy |
| Ollama | Unlimited | Slow | Complex |

**Why Groq for this project:**
- ✅ Generous free tier
- ✅ Fastest inference
- ✅ Great models (Llama 3.1)
- ✅ Perfect for portfolios

---

## 📁 Project Structure

```
backend/
├── config.py              # API keys, model config
├── document_manager.py    # Upload/delete documents
├── rag_engine.py          # RAG logic with Groq
└── main.py                # FastAPI endpoints

frontend/
└── app.py                 # Streamlit UI

data/
├── uploads/               # Stored documents
└── vectorstore/           # FAISS index
```

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** - Already in .gitignore
2. **Rotate API keys** - If exposed, regenerate immediately
3. **Use environment variables** - Never hardcode keys
4. **Monitor usage** - Check Groq dashboard regularly
5. **Implement auth** - For production deployments

---

## 🐛 Common Issues & Solutions

### Issue: "Authentication error"
**Solution:** Check your `.env` file has the correct API key

### Issue: "Slow first query"
**Solution:** Normal - embeddings model loading (happens once)

### Issue: "Context too long"
**Solution:** Reduce `CHUNK_SIZE` or `TOP_K_RESULTS` in config

### Issue: "Empty responses"
**Solution:** Make sure documents are properly indexed

---

## 🎯 Future Enhancements

- [ ] Support for more file types (DOCX, XLSX)
- [ ] Multi-document queries
- [ ] Conversation memory across sessions
- [ ] Advanced filters (date, author, etc.)
- [ ] Export Q&A history
- [ ] Support for images in PDFs

---

## 🤝 Contributing

This is a portfolio project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---

## 📄 License

MIT License - Free to use for personal/commercial projects

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com) - RAG framework
- [Groq](https://groq.com) - Lightning-fast LLM inference
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [Streamlit](https://streamlit.io) - UI framework
- [HuggingFace](https://huggingface.co) - Free embeddings

---

## 📞 Support

**Questions?** Open an issue on GitHub

**Need help with Groq?** Visit [docs.groq.com](https://docs.groq.com)

---

**⭐ Star this repo if it helped you!**

Made with ❤️ using Groq's free tier