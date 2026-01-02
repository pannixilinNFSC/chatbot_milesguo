# Google Cloud Functions Deployment

Deploy to Cloud Functions (2nd gen) using `main.py` which contains the FastAPI app and automatically starts a server listening on PORT.

## Prerequisites

1. Google Cloud Project with billing enabled
2. Cloud Functions API enabled
3. Google Cloud SDK (`gcloud`) installed and authenticated

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Deploy

### Deploy Script to Gcloud Functions

Run the deployment script:
```bash
bash scripts/deploy.sh
```

**Notes:**
- The same deployment command can be used for both initial deployment and updates
- Only changed configurations will be updated (code changes, environment variables, etc.)
- The function URL remains the same after updates


### Environment Variables

Required (set in `.env`):
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google/Gemini API key
- `ELASTIC_URL`: Elasticsearch server URL
- `ELASTIC_API_KEY`: Elasticsearch API key

Optional:
- `API_AUTH_TOKEN`: If set, `/chatbot`, `/search`, `/search_naive` require `Authorization: Bearer <token>`
- `CORS_ALLOW_ORIGINS`: "*" or comma-separated origins (e.g., "https://example.com,https://www.example.com")


## Notes

- Uses `main.py` which contains the FastAPI app
- Cloud Functions 2nd gen runs `main.py` as script (no `--entry-point` needed)
- The server starts in `if __name__ == "__main__"` block and listens on PORT (default 8080)
- Cloud Functions 2nd gen runs on Cloud Run and automatically sets PORT environment variable
- Cloud Functions 2nd gen supports longer timeouts (up to 3600s)
- Memory and CPU scale automatically based on configuration

