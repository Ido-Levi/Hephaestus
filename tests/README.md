# Hephaestus Integration Tests

This directory contains comprehensive integration tests for the Hephaestus RAG system. These are **real tests** that make actual API calls and interact with live services - no mocks!

## 🧪 Test Modules

### 1. **test_vector_store.py**
Tests Qdrant vector database operations:
- Storing embeddings with 3072 dimensions
- Similarity search
- Cross-collection search
- Filtered search
- Collection statistics
- Memory deletion

### 2. **test_rag_system.py**
Tests the RAG (Retrieval Augmented Generation) system:
- Task-based memory retrieval
- Similar task search
- Error solution search
- Domain knowledge retrieval
- Document ingestion
- Memory ranking and reranking

### 3. **test_mcp_server.py**
Tests MCP server endpoints:
- Health check endpoint
- Task creation
- Memory saving
- Task status updates
- Agent status monitoring
- Task progress tracking
- Server-Sent Events (SSE) connection

### 4. **test_llm_interface.py**
Tests OpenAI API integration:
- Embedding generation with text-embedding-3-large (3072 dimensions)
- Task enrichment with GPT-5
- Agent state analysis
- Agent prompt generation
- Error handling and fallback behavior

## 🚀 Running Tests

### Prerequisites
1. **Qdrant** must be running:
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

2. **Environment variables** in `.env`:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `LLM_MODEL` - Set to `gpt-5` (or another model)
   - `EMBEDDING_MODEL` - Set to `text-embedding-3-large`

3. **MCP Server** (optional, for server tests):
   ```bash
   python run_server.py
   ```

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Quick Smoke Test
```bash
python tests/run_all_tests.py --quick
```

### Run Specific Test Module
```bash
# Run just vector store tests
python tests/test_vector_store.py

# Or using the runner
python tests/run_all_tests.py --module test_vector_store.py
```

## 📊 What Gets Tested

### Real API Calls
- ✅ OpenAI embeddings API (text-embedding-3-large)
- ✅ OpenAI chat completions API (GPT-5 with fallback)
- ✅ Qdrant vector database operations
- ✅ MCP server HTTP endpoints

### Vector Dimensions
- All tests validate 3072-dimensional vectors
- Proper handling of text-embedding-3-large output
- Fallback to zero vectors on error

### Async Operations
- All vector store methods are properly async
- No "await" expression errors
- Proper async/await throughout the test suite

### Error Handling
- Invalid API keys
- Empty inputs
- Network failures
- Service unavailability

## ⚠️ Important Notes

1. **These tests use real API calls** - they will consume OpenAI API credits
2. **GPT-5 doesn't exist yet** - OpenAI will handle fallback, but some enrichment tests may fail
3. **Tests create and delete real data** in Qdrant
4. **Network connectivity required** for all tests

## 🔍 Troubleshooting

### Vector Dimension Errors
If you see "expected dim: 1536, got 3072":
1. Run `python reset_qdrant_collections.py` to recreate collections
2. Ensure `.env` has `EMBEDDING_MODEL=text-embedding-3-large`

### API Parameter Errors
If you see "max_tokens vs max_completion_tokens" errors:
- The code now uses `max_completion_tokens` for GPT-5 compatibility

### Async/Await Errors
If you see "object list can't be used in 'await' expression":
- All vector store methods are now async and should work properly

## 📈 Expected Results

When all systems are properly configured:
- ✅ Vector Store Tests: Should all pass
- ✅ RAG System Tests: Should all pass
- ✅ LLM Interface Tests: May have warnings due to GPT-5
- ✅ MCP Server Tests: Pass if server is running

## 🎯 Test Coverage

These integration tests cover:
- **Vector operations**: Store, search, delete with 3072-dim vectors
- **RAG retrieval**: Memory retrieval, ranking, and reranking
- **API integration**: Embeddings and chat completions
- **Server endpoints**: All MCP server REST APIs
- **Error scenarios**: Fallback behavior and error handling