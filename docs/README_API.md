# API Documentation

Base URL: `http://127.0.0.1:8080` (default port, configurable via `PORT` environment variable)

## Endpoints

### `GET /`
```json
{"message": "chatbot milesguo backend"}
```

### `GET /version`
```json
{"message": "v0.0.1"}
```

### `GET /token`
Public endpoint to get the auth token for frontend auto-configuration.

**Response:**
```json
{"token": "<API_AUTH_TOKEN>"}
```
or
```json
{"token": null}
```
if authentication is not enabled.

## Authentication (optional)

If `API_AUTH_TOKEN` is set on the server, the following endpoints require a Bearer token:
- `GET /search_naive`
- `GET /search`
- `GET /chatbot`
- `GET /agentic_rag`

Send the header:
`Authorization: Bearer <API_AUTH_TOKEN>`

For quick manual testing (e.g., pasting a URL in a browser), you can also pass:
`?token=<API_AUTH_TOKEN>`

Note: Query-string tokens are easier to accidentally leak (logs/referrers). Prefer the Authorization header in real clients.

### `GET /search_naive`
Simple search without query expansion.

**Parameters:**
- `txt_query` (string, required)
- `chunk_index` (string, required) - Index name for chunks (e.g., "data_miles", "data_lzj")
- `k` (int, default: 10)

**Response:** Array of search results with fields: `chunk_id`, `doc_id`, `text`, `context`, `doc_summary`, `doc_title`, `question1`, `_score`

### `GET /search`
Two-step search with query expansion.

**Parameters:**
- `txt_query` (string, required)
- `chunk_index` (string, required) - Index name for chunks (e.g., "data_miles", "data_lzj")
- `title_k` (int, default: 3)
- `chunk_k` (int, default: 12)
- `query_expand_k` (int, default: 1) - Number of query expansion iterations

**Response:** Array of search results

### `GET /chatbot`
RAG-based chatbot response.

**Parameters:**
- `txt_query` (string, required)
- `chunk_index` (string, required) - Index name for chunks (e.g., "data_miles", "data_lzj")
- `query_context` (list[string], optional) - Conversation history (typically last Q&A pair, limited to last 4 items)
- `title_k` (int, default: 3)
- `chunk_k` (int, default: 12)
- `query_expand_k` (int, default: 1) - Number of query expansion iterations

**Response:**
```json
{
  "content": "LLM response",
  "search_results": [...],
  "prompt": "..."
}
```

### `GET /agentic_rag`
Agentic RAG-based chatbot response with iterative search refinement.

**Parameters:**
- `txt_query` (string, required)
- `chunk_index` (string, required) - Index name for chunks (e.g., "data_miles", "data_lzj")
- `query_context` (list[string], optional) - Conversation history
- `title_k` (int, default: 3)
- `chunk_k` (int, default: 12)
- `query_expand_k` (int, default: 1) - Maximum number of query expansion iterations
- `max_iter` (int, default: 2) - Maximum number of search iterations

**Response:**
```json
{
  "content": "LLM response",
  "search_results": [...],
  "historical_search_ops": [...],
  "query_type": "...",
  "search_count": 1
}
```

## Examples

```bash
# Load token from .env file (if authentication is enabled)
# In bash/WSL:
source .env
# Then use $API_AUTH_TOKEN in curl commands

# Recommended: Use -G with --data-urlencode for proper URL encoding (handles Chinese characters)
curl -G "http://127.0.0.1:8080/search_naive" \
  --data-urlencode "txt_query=郭文贵" \
  --data-urlencode "chunk_index=data_miles" \
  --data-urlencode "k=10" \
  --data-urlencode "token=$API_AUTH_TOKEN"

curl -G "http://127.0.0.1:8080/search" \
  --data-urlencode "txt_query=爆料革命" \
  --data-urlencode "chunk_index=data_miles" \
  --data-urlencode "title_k=3" \
  --data-urlencode "chunk_k=12" \
  --data-urlencode "query_expand_k=1" \
  --data-urlencode "token=$API_AUTH_TOKEN"

curl -G "http://127.0.0.1:8080/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "chunk_index=data_miles" \
  --data-urlencode "token=$API_AUTH_TOKEN"

# With query_context (conversation history):
curl -G "http://127.0.0.1:8080/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "chunk_index=data_miles" \
  --data-urlencode "query_context=用户: 郭文贵是谁" \
  --data-urlencode "query_context=助手: 郭文贵是..." \
  --data-urlencode "token=$API_AUTH_TOKEN"

# Agentic RAG endpoint:
curl -G "http://127.0.0.1:8080/agentic_rag" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "chunk_index=data_miles" \
  --data-urlencode "max_iter=2" \
  --data-urlencode "token=$API_AUTH_TOKEN"

# Or use Authorization header (also handles Chinese properly):
curl -G "http://127.0.0.1:8080/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "chunk_index=data_miles" \
  -H "Authorization: Bearer $API_AUTH_TOKEN"

# Cloud Functions example:
curl -G "https://us-central1-xixibaigao.cloudfunctions.net/chatbot-milesguo/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "chunk_index=data_miles" \
  --data-urlencode "token=$API_AUTH_TOKEN"
```

```python
import requests

# Basic request
response = requests.get("http://127.0.0.1:8080/chatbot", params={
    "txt_query": "什么是新中国联邦?",
    "chunk_index": "data_miles"
})
print(response.json()["content"])

# With query_context (conversation history)
response = requests.get("http://127.0.0.1:8080/chatbot", params={
    "txt_query": "什么是新中国联邦?",
    "chunk_index": "data_miles",
    "query_context": ["用户: 郭文贵是谁", "助手: 郭文贵是..."]
})
print(response.json()["content"])

# Agentic RAG request
response = requests.get("http://127.0.0.1:8080/agentic_rag", params={
    "txt_query": "什么是新中国联邦?",
    "chunk_index": "data_miles",
    "max_iter": 2
})
print(response.json()["content"])
print(f"Search count: {response.json()['search_count']}")
```

## Error Response

```json
{"detail": "Error message"}
```

