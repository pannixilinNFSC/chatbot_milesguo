# Google Cloud Functions Deployment

Deploy to Cloud Functions (2nd gen) using `main_gcf.py` as entry point, which wraps the FastAPI app from `server.py`.

## Prerequisites

1. Google Cloud Project with billing enabled
2. Cloud Functions API enabled
3. Google Cloud SDK (`gcloud`) installed and authenticated

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Deploy

### Deploy Function

Load environment variables from `.env` file:

```bash
# Load .env file and deploy
export $(cat .env | grep -v '^#' | xargs) && \
gcloud functions deploy chatbot-milesguo \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --entry-point main_gcf.cloud_function \
  --trigger-http \
  --allow-unauthenticated \
  --memory 256Mi \
  --timeout 300s \
  --max-instances 10 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,GOOGLE_API_KEY=$GOOGLE_API_KEY,ELASTIC_URL=$ELASTIC_URL,ELASTIC_API_KEY=$ELASTIC_API_KEY
```


## Environment Variables

Set via CLI:
```bash
gcloud functions deploy chatbot-milesguo \
  --gen2 \
  --region us-central1 \
  --update-env-vars KEY=VALUE
```

Or via console: Cloud Functions → chatbot-milesguo → Configuration → Environment variables

## Using Secret Manager

1. Create secrets (same as Cloud Run):
```bash
echo -n "your-api-key" | gcloud secrets create openai-api-key --data-file=-
```

2. Deploy with secrets:
```bash
gcloud functions deploy chatbot-milesguo \
  --gen2 \
  --region us-central1 \
  --update-secrets OPENAI_API_KEY=openai-api-key:latest,ELASTIC_URL=elastic-url:latest,ELASTIC_API_KEY=elastic-api-key:latest
```

## Get Function URL

```bash
gcloud functions describe chatbot-milesguo --gen2 --region us-central1 --format 'value(serviceConfig.uri)'
```

## Notes

- Uses `main_gcf.py` as entry point, which wraps `server.py` FastAPI app
- Entry point format: `module_name.function_name` (e.g., `main_gcf.cloud_function`)
- Cloud Functions 2nd gen supports longer timeouts (up to 3600s)
- Memory and CPU scale automatically based on configuration
- No need to manage containers or ports

