# ContextForge - RAG Agent System

A production-ready Retrieval-Augmented Generation (RAG) system that ingests PDF documents, processes them into searchable chunks, and provides intelligent question-answering with page-level citations.

## 🚀 Features

- **PDF Processing**: Handles PDFs from small to 1000+ pages
- **Intelligent Chunking**: Sentence-aware text chunking with configurable overlap
- **Vector Search**: Qdrant-based vector storage with OpenAI embeddings
- **Smart Retrieval**: Advanced document retrieval with deduplication and confidence scoring
- **Citation Support**: Page-level citations for all answers
- **Background Processing**: Redis-based job queue for large document ingestion
- **RESTful API**: FastAPI-based API ready for web/mobile clients
- **Modular Architecture**: Pluggable interfaces for easy customization

## 🏗️ Architecture

```
ContextForge/
├── app/                    # FastAPI application
│   ├── api/               # API routes and schemas
│   ├── core/              # Configuration and utilities
│   ├── db/                # Database models and repository
│   ├── services/          # Core RAG services
│   │   ├── parser/        # PDF parsing (PyMuPDF)
│   │   ├── chunker/       # Text chunking
│   │   ├── embeddings/    # OpenAI embeddings
│   │   ├── vectorstore/   # Qdrant vector storage
│   │   ├── retriever/     # Document retrieval
│   │   ├── reranker/      # Optional LLM reranking
│   │   └── answerer/      # Response generation
│   └── workers/           # Background job processing
├── data/                  # Document storage and metadata
├── tests/                 # Test suite
└── docker-compose.yml     # Infrastructure setup
```

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Database**: SQLite (metadata), Qdrant (vectors)
- **Queue**: Redis + RQ
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: OpenAI GPT models
- **PDF Processing**: PyMuPDF (fitz)
- **Containerization**: Docker + Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Git

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd ragagent_understanding
```

### 2. Environment Configuration

```bash
cd ContextForge
cp .env.sample .env
# Edit .env with your OpenAI API key and other settings
```

### 3. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- Qdrant (vector database) on port 6333
- Redis (job queue) on port 6379

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
# Terminal 1: Start the API server
make run

# Terminal 2: Start the background worker
make worker
```

The API will be available at `http://localhost:8080`

### 6. API Documentation

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## 📚 Usage

### Upload a Document

```bash
curl -X POST "http://localhost:8080/v1/documents" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

### Ask a Question

```bash
curl -X POST "http://localhost:8080/v1/answers" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic of this document?",
    "docIds": ["your-document-id"],
    "topK": 10
  }'
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# OpenAI
OPENAI_API_KEY=your_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini

# Processing
CHUNK_TARGET_TOKENS=800
CHUNK_OVERLAP_TOKENS=100
MAX_CONTEXT_TOKENS=2000

# Features
ENABLE_RERANK=false
ENABLE_OCR=false
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_chunker.py -v
```

## 📁 Project Structure

- **`app/api/`**: REST API endpoints
- **`app/services/`**: Core RAG services
- **`app/workers/`**: Background job processing
- **`app/db/`**: Database models and operations
- **`data/`**: Document storage and metadata database

## 🔄 Workflow

1. **Document Upload**: PDF is uploaded via API
2. **Processing**: Background worker parses, chunks, and embeds the document
3. **Storage**: Chunks are stored in Qdrant with metadata
4. **Query**: User asks a question
5. **Retrieval**: System finds relevant chunks using vector similarity
6. **Answer**: LLM generates response with citations
7. **Response**: Answer returned with confidence metrics

## 🚧 Development

### Code Quality

```bash
# Format code
make fmt

# Lint code
make lint
```

### Adding New Features

- Follow the existing service pattern
- Implement interfaces for pluggable components
- Add comprehensive tests
- Update documentation

## 📊 Performance

- **Chunking**: ~800 tokens per chunk with 100 token overlap
- **Embedding**: Batch processing for efficiency
- **Search**: Configurable top-K retrieval with deduplication
- **Response**: Context-aware answer generation

## 🔒 Security

- CORS enabled for web clients
- Input validation on all endpoints
- Structured error handling
- No sensitive data in logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

[Add your license here]

## 🆘 Support

For issues and questions:
- Check the documentation
- Review existing issues
- Create a new issue with detailed information

## 🔮 Roadmap

- [ ] Multi-modal document support
- [ ] Advanced OCR integration
- [ ] Conversation memory
- [ ] Document versioning
- [ ] Export capabilities
- [ ] Authentication system
- [ ] Performance monitoring
- [ ] Multi-language support

---

**Built with ❤️ for intelligent document understanding**
