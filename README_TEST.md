# Test Suite

Unit tests for the chatbot_milesguo project. All external dependencies (Elasticsearch, LiteLLM API, file I/O) are mocked.

## Setup

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

Run all tests:

```bash
pytest test/
```

Run specific test file:

```bash
pytest test/test_security.py
pytest test/test_rag_base.py
```

Run with verbose output:

```bash
pytest test/ -v
```

Run with coverage:

```bash
pytest test/ --cov=. --cov-report=html
```

## Test Files

- `test/test_security.py`: Tests for security module (authentication, CORS, exception handling)
- `test/test_rag_base.py`: Tests for RAGBase class (search, deduplication, chat functionality)

## Mocked Dependencies

The following external dependencies are mocked in tests:

- **Elasticsearch**: All Elasticsearch client calls are mocked
- **LiteLLM API**: LLM API calls are mocked
- **File I/O**: `prompt.json` file reading is mocked
- **Environment variables**: Tested with mocked environment variables

