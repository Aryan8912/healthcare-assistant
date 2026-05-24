# 🏥 MedAssist AI — Healthcare Appointment Assistant

An AI-powered healthcare front-desk assistant with multi-agent orchestration, RAG retrieval, appointment management, and multilingual support.

<img width="1920" height="1080" alt="Screenshot (12)" src="https://github.com/user-attachments/assets/eb8f02d3-38ff-439b-9ba4-b6209cab4bbf" />
<img width="1920" height="1080" alt="Screenshot (11)" src="https://github.com/user-attachments/assets/8fb1609a-e62f-4ee4-9abe-2008d3c874f2" />
<img width="1920" height="1080" alt="Screenshot (10)" src="https://github.com/user-attachments/assets/cac0113c-fd8d-4332-b25e-804e29abdafb" />
<img width="1920" height="1080" alt="Screenshot (9)" src="https://github.com/user-attachments/assets/882af89b-fe1e-4610-aa30-da7b1859e8e5" />
<img width="1920" height="1080" alt="Screenshot (7)" src="https://github.com/user-attachments/assets/1dc4286f-974e-4516-92be-3e2b3b89c1ad" />


---

## 🎯 Features

| Feature | Description |
|---|---|
| 💬 AI Chat | Multi-turn conversations with context memory |
| 📅 Appointments | Book, cancel, reschedule appointments |
| 🔍 RAG Pipeline | Medical Q&A from knowledge base |
| 🧩 Multi-Agent | LangGraph workflow with 5 agents |
| 📄 Documents | Upload & analyze PDFs and medical images |
| 🌐 Multilingual | Hindi, Tamil, Malayalam, mixed language support |
| ⚙️ Tool Calling | Visual tool execution indicators in UI |
| 📊 Benchmarks | DeepEval LLM-as-judge evaluation |

---

## 🏗️ Architecture

```
User Message
     │
     ▼
Router Agent (Gemini)
     │
     ├──► Appointment Agent  → fetch_slots, book, cancel, reschedule
     ├──► RAG Agent          → FAISS search + Gemini generation
     ├──► Summary Agent      → conversation summarization
     ├──► Document Agent     → PDF/image analysis
     └──► General Agent      → multilingual greetings
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini (gemini-2.0-flash-lite) |
| Embeddings | Gemini (models/gemini-embedding-001) |
| Agent Framework | LangGraph |
| Backend | FastAPI (Python) |
| Vector DB | FAISS |
| Database | SQLite (SQLAlchemy) |
| Frontend | React + Vite + Tailwind CSS |
| Evaluation | DeepEval |
| API Docs | Swagger UI |

---

## 📁 Project Structure

```
healthcare-assistant/
├── backend/
│   ├── agents/          # 5 AI agents
│   ├── api/             # FastAPI endpoints
│   ├── db/              # Database models & seed
│   ├── evaluation/      # DeepEval benchmarks
│   ├── graph/           # LangGraph workflow
│   ├── modules/         # Core modules
│   ├── rag/             # FAISS + knowledge base
│   ├── tests/           # Test suite (46 tests)
│   ├── tools/           # Tool functions
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/  # Chat UI components
    │   ├── hooks/       # React hooks
    │   ├── lib/         # API client
    │   └── pages/       # Chat & Appointments pages
    └── package.json
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key (free at https://aistudio.google.com/apikey)

### Backend Setup

```bash
# Clone repo
git clone https://github.com/Aryan8912/healthcare-assistant.git
cd healthcare-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your GOOGLE_API_KEY

# Run backend
uvicorn backend.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access
- **Chat UI** → http://localhost:5173
- **API Docs** → http://localhost:8000/docs
- **Health** → http://localhost:8000/health

---

## 🔑 Environment Variables

Create `backend/.env` with:

```env
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_MODEL=models/gemini-2.0-flash-lite
EMBEDDING_MODEL=models/gemini-embedding-001
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Main chat with agent routing |
| GET | `/api/doctors` | List all doctors |
| GET | `/api/appointments/slots` | Get available slots |
| POST | `/api/appointments/book` | Book appointment |
| DELETE | `/api/appointments/{id}` | Cancel appointment |
| GET | `/api/appointments/history/{phone}` | Patient history |
| POST | `/api/documents/upload` | Upload PDF/image |
| POST | `/api/documents/analyze/{id}` | Analyze document |
| GET | `/docs` | Swagger UI |

---

## 🧩 Multi-Agent Workflow

```python
# Example: Book an appointment via chat
POST /api/chat
{
  "message": "I want to book an appointment with a cardiologist",
  "session_id": "optional-session-id"
}

# Response
{
  "session_id": "uuid",
  "response": "I can help! Here are available doctors...",
  "agent_used": "appointment_agent",
  "intent": "appointment",
  "tool_calls": [{"tool": "get_doctors", "status": "done"}]
}
```

---

## 🌐 Multilingual Support

```
English: "What are the symptoms of diabetes?"
Hindi:   "मधुमेह के लक्षण क्या हैं?"
Tamil:   "அப்பாயிண்ட்மென்ட் எப்படி பதிவு செய்வது?"
Mixed:   "I want to book appointment, मेरा नाम Aryan है"
```

---

## 📊 DeepEval Benchmarks

```bash
python -m backend.evaluation.benchmarks
```

| Benchmark | Description |
|---|---|
| Answer Relevancy | Response relevant to query |
| Faithfulness | Answer grounded in context |
| Contextual Recall | Right chunks retrieved |
| Hallucination | No fabricated information |
| Document Understanding | PDF/image analysis quality |
| Multilingual Support | Cross-language response quality |

---

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run specific test
python -m pytest backend/tests/test_scheduler.py -v

# Run demos
python -m backend.tests.final_demo
python -m backend.tests.quick_start
python -m backend.tests.display_summary
```

---

## 📸 Screenshots

### Chat Interface
- Multi-agent routing with visual tool call badges
- Real-time agent trace display
- Document upload support

### Appointment Booking
- Step-by-step booking flow
- Doctor selection with availability
- Time slot management

---

## 🙏 Acknowledgements

- [LangGraph](https://github.com/langchain-ai/langgraph) — Multi-agent orchestration
- [Google Gemini](https://ai.google.dev) — LLM and embeddings
- [FAISS](https://github.com/facebookresearch/faiss) — Vector similarity search
- [DeepEval](https://github.com/confident-ai/deepeval) — LLM evaluation
- [FastAPI](https://fastapi.tiangolo.com) — Backend framework
