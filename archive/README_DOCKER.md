# Docker Deployment for Google Cloud Run

This directory contains Docker configuration files for deploying the chatbot to Google Cloud Run.

## Files

- `Dockerfile`: Container image definition
- `.dockerignore`: Files to exclude from Docker build context
- `cloudbuild.yaml`: Google Cloud Build configuration for automated deployment

## Prerequisites

1. Google Cloud Project with Cloud Run API enabled
2. Docker installed locally (for local testing)
3. Google Cloud SDK (gcloud) installed and configured
4. Environment variables set in Cloud Run:
   - `OPENAI_API_KEY`: OpenAI API key
   - `GOOGLE_API_KEY`: Google/Gemini API key (optional)
   - `ELASTIC_URL`: Elasticsearch server URL
   - `ELASTIC_API_KEY`: Elasticsearch API key

## Local Testing

Build the Docker image locally:

```bash
docker build -t chatbot-milesguo -f docker/Dockerfile .
```

Run the container locally:

```bash
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e OPENAI_API_KEY=your_key \
  -e GOOGLE_API_KEY=your_key \
  -e ELASTIC_URL=your_url \
  -e ELASTIC_API_KEY=your_key \
  chatbot-milesguo
```

## Deploy to Cloud Run

### Option 1: Using Cloud Build (Recommended)

```bash
gcloud builds submit --config docker/cloudbuild.yaml
```

### Option 2: Manual Deployment

1. Build and push the image:

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Build the image
docker build -t gcr.io/$PROJECT_ID/chatbot-milesguo:latest -f docker/Dockerfile .

# Push to Container Registry
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
  --set-env-vars OPENAI_API_KEY=your_key,GOOGLE_API_KEY=your_key,ELASTIC_URL=your_url,ELASTIC_API_KEY=your_key
```

## Environment Variables

Set these in Cloud Run console or via gcloud:

- `OPENAI_API_KEY`: Required for OpenAI API
- `GOOGLE_API_KEY`: Optional, for Gemini fallback
- `ELASTIC_URL`: Required for Elasticsearch
- `ELASTIC_API_KEY`: Required for Elasticsearch
- `PORT`: Automatically set by Cloud Run (default: 8080)

## Notes

- Cloud Run automatically sets the `PORT` environment variable
- The application listens on `0.0.0.0` to accept connections from Cloud Run
- Make sure your Elasticsearch instance is accessible from Cloud Run's network

