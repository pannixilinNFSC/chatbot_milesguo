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
curl "http://127.0.0.1:7711/search_naive?txt_query=郭文贵&k=10"
curl "http://127.0.0.1:7711/search?txt_query=爆料革命&title_k=3&chunk_k=10"
curl "https://us-central1-xixibaigao.cloudfunctions.net/chatbot-milesguo/chatbot?txt_query=什么是爆料革命"
```

```python
import requests
response = requests.get("http://127.0.0.1:7711/chatbot", params={"txt_query": "什么是新中国联邦?"})
print(response.json()["content"])
```

## Error Response

```json
{"detail": "Error message"}
```

