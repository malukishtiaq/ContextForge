# 🚀 ContextForge RAG System - Demo Guide

## 🎯 Demo Overview
This guide will help you demonstrate the ContextForge RAG system during your presentation. The system processes PDF documents, breaks them into intelligent chunks, and provides accurate answers with page-level citations.

## 🔧 Current Status
✅ **Infrastructure Running**: Qdrant (vector DB) + Redis (job queue)  
✅ **API Server**: Running on http://localhost:8080  
✅ **Background Worker**: Processing jobs  
✅ **Project Structure**: Fixed and pushed to GitHub  

## 📋 Demo Flow

### 1. **System Overview** (2-3 minutes)
- **What it does**: PDF → Chunks → Embeddings → Vector Search → Q&A with Citations
- **Architecture**: FastAPI + Qdrant + Redis + OpenAI
- **Key Features**: Intelligent chunking, deduplication, confidence scoring

### 2. **Live Demo** (5-7 minutes)

#### Step 1: Show API Health
```bash
curl http://localhost:8080/v1/health
```
**Expected**: `{"status":"ok"}`

#### Step 2: Show API Documentation
- Open browser: http://localhost:8080/docs
- Point out the three main endpoints:
  - `POST /v1/documents` - Upload PDFs
  - `GET /v1/documents/{id}` - Check status
  - `POST /v1/answers` - Ask questions

#### Step 3: Upload a Document
```bash
# You can use any PDF, or create one from the demo_document.txt
curl -X POST "http://localhost:8080/v1/documents" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@demo_document.txt"
```
**Expected**: Returns document ID and status

#### Step 4: Check Processing Status
```bash
curl "http://localhost:8080/v1/documents/{DOCUMENT_ID}"
```
**Expected**: Shows processing progress (queued → processing → ready)

#### Step 5: Ask Questions
```bash
curl -X POST "http://localhost:8080/v1/answers" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key features of ContextForge?",
    "docIds": ["YOUR_DOC_ID"],
    "topK": 10
  }'
```

### 3. **Key Talking Points**

#### Technical Highlights
- **Modular Architecture**: Each service (parser, chunker, embedder) is pluggable
- **Intelligent Chunking**: Sentence-aware with configurable overlap
- **Vector Search**: Qdrant for fast similarity search
- **Background Processing**: Redis queue for large document ingestion
- **Citation System**: Page-level references for all answers

#### Business Value
- **Scalability**: Handles documents from small to 1000+ pages
- **Accuracy**: Confidence scoring and deduplication
- **Flexibility**: Easy to swap AI providers
- **Production Ready**: Dockerized, tested, documented

## 🎭 Demo Script

### Opening
"Today I'm demonstrating ContextForge, a production-ready RAG system that transforms how we interact with documents. It's not just another PDF reader - it's an intelligent system that understands context and provides accurate answers with proper citations."

### During Demo
1. **Show the architecture**: "Here's our modular system - each component can be swapped out independently"
2. **Upload process**: "Watch how the system processes this document in the background"
3. **Q&A demonstration**: "Now let's ask it questions and see how it provides answers with citations"
4. **Technical details**: "The system uses vector similarity to find the most relevant chunks"

### Closing
"ContextForge demonstrates how modern AI can make document analysis not just faster, but more intelligent. It's ready for production use and can scale to handle enterprise document volumes."

## 🚨 Troubleshooting

### If API doesn't respond:
```bash
# Check if server is running
ps aux | grep uvicorn

# Restart if needed
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### If worker isn't processing:
```bash
# Check Redis connection
redis-cli ping

# Restart worker
python3 -m rq worker --url redis://localhost:6379/0 ingest
```

### If services aren't running:
```bash
# Restart Docker services
docker compose down && docker compose up -d
```

## 📱 Demo Tips

1. **Have a backup plan**: If live demo fails, show the code structure and explain the architecture
2. **Keep it simple**: Focus on the core functionality, not every technical detail
3. **Show the process**: Demonstrate the full pipeline from upload to answer
4. **Highlight citations**: This is a key differentiator from other systems
5. **Be prepared for questions**: Know the technical stack and architecture decisions

## 🔗 Useful URLs

- **API**: http://localhost:8080
- **Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/v1/health
- **GitHub**: https://github.com/malukishtiaq/ContextForge

## 🎯 Success Metrics

Your demo is successful if you can:
- ✅ Upload a document and see it processed
- ✅ Ask a question and get an answer with citations
- ✅ Explain the key technical components
- ✅ Demonstrate the business value

## 🚀 Next Steps After Demo

1. **Get feedback** on the system
2. **Identify use cases** for potential clients
3. **Plan improvements** based on feedback
4. **Consider deployment** options (cloud, on-premise)

---

**Good luck with your demo! 🎉**

Remember: You're not just showing code - you're demonstrating the future of document intelligence.
