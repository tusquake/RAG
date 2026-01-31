# AI-Powered Document & Multimedia Q&A Application

A production-ready, full-stack AI application that enables intelligent Q&A, summarization, and timestamp extraction from documents, audio, and video files.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)

## Features

- **Multi-format Support**: Upload PDFs, audio (MP3, WAV, M4A), and video (MP4, WebM) files
- **AI-Powered Q&A**: Ask questions about your documents and get intelligent answers
- **Audio/Video Transcription**: Automatic transcription with word-level timestamps using Whisper
- **Semantic Search**: Find relevant content using FAISS vector similarity
- **Timestamp Navigation**: Click timestamps to jump to specific moments in audio/video
- **Document Summarization**: Generate AI-powered summaries of your content
- **Real-time Streaming**: SSE-based streaming responses for chat
- **Secure Authentication**: JWT-based authentication with rate limiting

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────────┐   │
│  │  Auth   │  │ Dashboard │  │  Chat   │  │   Media Player   │   │
│  └─────────┘  └──────────┘  └─────────┘  └──────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API / SSE
┌──────────────────────────────┴──────────────────────────────────┐
│                       Backend (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      API Layer                              │ │
│  │   Auth │ Upload │ Documents │ Chat (Q&A, Summary, Stream)  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    AI Services                              │ │
│  │   Whisper │ Embeddings │ FAISS │ RAG Pipeline │ LLM (HF)   │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                              │
   ┌────┴────┐                                   ┌────┴────┐
   │ MongoDB │                                   │  Redis  │
   │ (Data)  │                                   │ (Cache) │
   └─────────┘                                   └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- MongoDB Atlas account (or local MongoDB)
- HuggingFace API key

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd RAG
   ```

2. **Backend configuration**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Frontend configuration**
   ```bash
   cd frontend
   cp .env.example .env
   ```

### Local Development

#### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Manual Setup

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## API Documentation

Once the backend is running, access the interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get token |
| POST | `/api/upload/pdf` | Upload PDF document |
| POST | `/api/upload/audio` | Upload audio file |
| POST | `/api/upload/video` | Upload video file |
| GET | `/api/documents` | List documents |
| POST | `/api/chat` | Ask question about document |
| POST | `/api/chat/stream` | Stream AI response (SSE) |
| POST | `/api/chat/summarize` | Get document summary |
| POST | `/api/chat/timestamps` | Search for timestamps |

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `document_qa` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `JWT_SECRET` | Secret key for JWT tokens | (required) |
| `HUGGINGFACE_API_KEY` | HuggingFace API key | (required) |
| `WHISPER_MODEL` | Whisper model size | `base` |
| `MAX_FILE_SIZE_MB` | Maximum upload size | `100` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `/api` |

## Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm test

# With coverage
npm run test:coverage
```

## Deployment

### Render Deployment

1. Create a new Web Service for the backend
2. Create a new Static Site for the frontend
3. Add environment variables in Render dashboard
4. Configure deploy hooks for CI/CD

### Environment Variables for Production

Ensure these are set in your production environment:
- `JWT_SECRET`: Strong random string
- `HUGGINGFACE_API_KEY`: Your API key
- `MONGODB_URI`: MongoDB Atlas connection string
- `REDIS_URL`: Redis cloud connection string

## Project Structure

```
RAG/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── middleware/     # Auth, rate limiting
│   │   │   └── routes/         # API endpoints
│   │   ├── db/                 # MongoDB, Redis
│   │   ├── models/             # Pydantic models
│   │   ├── services/           # AI services
│   │   └── utils/              # Helpers
│   ├── services/               # Core AI services
│   ├── tests/                  # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── context/            # Auth context
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   └── styles/             # CSS
│   ├── tests/                  # Frontend tests
│   ├── Dockerfile
│   └── package.json
├── .github/workflows/          # CI/CD
└── docker-compose.yml
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [HuggingFace](https://huggingface.co/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [React](https://react.dev/)
