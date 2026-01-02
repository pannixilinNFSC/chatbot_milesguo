# API Documentation

Base URL: `http://127.0.0.1:7711`

## Endpoints

### `GET /`
```json
{"message": "chatbot milesguo backend"}
```

### `GET /version`
```json
{"message": "v0.0.1"}
```

## Authentication (optional)

If `API_AUTH_TOKEN` is set on the server, the following endpoints require a Bearer token:
- `GET /search_naive`
- `GET /search`
- `GET /chatbot`

Send the header:
`Authorization: Bearer <API_AUTH_TOKEN>`

For quick manual testing (e.g., pasting a URL in a browser), you can also pass:
`?token=<API_AUTH_TOKEN>`

Note: Query-string tokens are easier to accidentally leak (logs/referrers). Prefer the Authorization header in real clients.

### `GET /search_naive`
Simple search without query expansion.

**Parameters:**
- `txt_query` (string, required)
- `k` (int, default: 10)

**Response:** Array of search results with fields: `chunk_id`, `doc_id`, `text`, `context`, `doc_summary`, `doc_title`, `question1`, `_score`

### `GET /search`
Two-step search with optional query expansion.

**Parameters:**
- `txt_query` (string, required)
- `title_k` (int, default: 3)
- `chunk_k` (int, default: 10)
- `expand_query` (bool, default: true)

**Response:** `[search_results, expanded_query]`

### `GET /chatbot`
RAG-based chatbot response.

**Parameters:**
- `txt_query` (string, required)
- `query_context` (list[string], optional) - Conversation history (typically last Q&A pair)
- `title_k` (int, default: 3)
- `chunk_k` (int, default: 10)
- `expand_query` (bool, default: true)

**Response:**
```json
{
  "content": "LLM response",
  "search_results": [...],
  "prompt": "..."
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
  --data-urlencode "k=10" \
  --data-urlencode "token=$API_AUTH_TOKEN"

curl -G "http://127.0.0.1:8080/search" \
  --data-urlencode "txt_query=爆料革命" \
  --data-urlencode "title_k=3" \
  --data-urlencode "chunk_k=10" \
  --data-urlencode "token=$API_AUTH_TOKEN"

curl -G "http://127.0.0.1:8080/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "token=$API_AUTH_TOKEN"

# With query_context (conversation history):
curl -G "http://127.0.0.1:8080/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "query_context=用户: 郭文贵是谁" \
  --data-urlencode "query_context=助手: 郭文贵是..." \
  --data-urlencode "token=$API_AUTH_TOKEN"

# Or use Authorization header (also handles Chinese properly):
curl -G "http://127.0.0.1:8080/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  -H "Authorization: Bearer $API_AUTH_TOKEN"

# Cloud Functions example:
curl -G "https://us-central1-xixibaigao.cloudfunctions.net/chatbot-milesguo/chatbot" \
  --data-urlencode "txt_query=什么是爆料革命" \
  --data-urlencode "token=$API_AUTH_TOKEN"
```

```python
import requests

# Basic request
response = requests.get("http://127.0.0.1:7711/chatbot", params={"txt_query": "什么是新中国联邦?"})
print(response.json()["content"])

# With query_context (conversation history)
response = requests.get("http://127.0.0.1:7711/chatbot", params={
    "txt_query": "什么是新中国联邦?",
    "query_context": ["用户: 郭文贵是谁", "助手: 郭文贵是..."]
})
print(response.json()["content"])
```

## Error Response

```json
{"detail": "Error message"}
```

