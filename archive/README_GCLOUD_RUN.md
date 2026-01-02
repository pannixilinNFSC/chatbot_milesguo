# Google Cloud Run Deployment

## Prerequisites

1. Google Cloud Project with billing enabled
2. Cloud Run API enabled
3. Google Cloud SDK (`gcloud`) installed and authenticated

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## Quick Deploy

### Option 1: Using Cloud Build (Recommended)

```bash
gcloud builds submit --config docker/cloudbuild.yaml
```

### Option 2: Manual Deploy

1. Build and push image:
```bash
export PROJECT_ID=your-project-id
docker build -t gcr.io/$PROJECT_ID/chatbot-milesguo:latest -f docker/Dockerfile .
docker push gcr.io/$PROJECT_ID/chatbot-milesguo:latest
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy chatbot-milesguo \
  --image gcr.io/$PROJECT_ID/chatbot-milesguo:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

3. Set environment variables:
```bash
gcloud run services update chatbot-milesguo \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=your_key,GOOGLE_API_KEY=your_key,ELASTIC_URL=your_url,ELASTIC_API_KEY=your_key
```

## Environment Variables

Required:
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google/Gemini API key (for fallback and query expansion; not recommended for reply generation due to political content moderation)
- `ELASTIC_URL`: Elasticsearch server URL
- `ELASTIC_API_KEY`: Elasticsearch API key

Set via console or CLI:
```bash
gcloud run services update chatbot-milesguo \
  --region us-central1 \
  --update-env-vars KEY=VALUE
```

## Using Secret Manager (Recommended for Production)

1. Create secrets:
```bash
echo -n "your-api-key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-elastic-url" | gcloud secrets create elastic-url --data-file=-
echo -n "your-elastic-key" | gcloud secrets create elastic-api-key --data-file=-
```

2. Grant Cloud Run access:
```bash
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

3. Deploy with secrets:
```bash
gcloud run deploy chatbot-milesguo \
  --image gcr.io/$PROJECT_ID/chatbot-milesguo:latest \
  --region us-central1 \
  --update-secrets OPENAI_API_KEY=openai-api-key:latest,ELASTIC_URL=elastic-url:latest,ELASTIC_API_KEY=elastic-api-key:latest
```

## Configuration

### Resource Limits
- Memory: 2Gi (adjust based on workload)
- CPU: 2 (required for memory > 1Gi)
- Timeout: 300s (for LLM API calls)
- Max instances: 10 (adjust based on traffic)

### Update Configuration
```bash
gcloud run services update chatbot-milesguo \
  --region us-central1 \
  --memory 4Gi \
  --cpu 1 \
  --timeout 600 \
  --max-instances 20
```

## Get Service URL

```bash
gcloud run services describe chatbot-milesguo --region us-central1 --format 'value(status.url)'
```

## View Logs

```bash
gcloud run services logs read chatbot-milesguo --region us-central1
```

## Notes

- Cloud Run automatically sets `PORT=8080`
- Application listens on `0.0.0.0` to accept connections
- Ensure Elasticsearch is accessible from Cloud Run (consider VPC connector for private IPs)
- Use Secret Manager for sensitive credentials in production

