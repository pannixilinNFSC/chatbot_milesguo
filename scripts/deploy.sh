#!/bin/bash
# Load .env file and deploy

set -e  # Exit on error

echo "=== Starting deployment to Google Cloud Functions ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with required environment variables."
    exit 1
fi

echo "Loading environment variables from .env file..."
# Load .env file more safely
set -a  # Automatically export all variables
source .env
set +a

# Verify required environment variables are set
if [ -z "$OPENAI_API_KEY" ] || [ -z "$GOOGLE_API_KEY" ] || [ -z "$ELASTIC_URL" ] || [ -z "$ELASTIC_API_KEY" ]; then
    echo "Warning: Some required environment variables may be missing!"
    echo "Required: OPENAI_API_KEY, GOOGLE_API_KEY, ELASTIC_URL, ELASTIC_API_KEY"
fi

echo "Deploying function (this may take 5-15 minutes)..."
echo "Function: chatbot-milesguo"
echo "Region: us-central1"
echo "Runtime: python311"
echo ""

# Build environment variables string
ENV_VARS="OPENAI_API_KEY=$OPENAI_API_KEY,GOOGLE_API_KEY=$GOOGLE_API_KEY,ELASTIC_URL=$ELASTIC_URL,ELASTIC_API_KEY=$ELASTIC_API_KEY"

# Add optional variables if they exist
if [ -n "$API_AUTH_TOKEN" ]; then
    ENV_VARS="$ENV_VARS,API_AUTH_TOKEN=$API_AUTH_TOKEN"
fi

if [ -n "$CORS_ALLOW_ORIGINS" ]; then
    ENV_VARS="$ENV_VARS,CORS_ALLOW_ORIGINS=$CORS_ALLOW_ORIGINS"
fi

# Deploy with verbose output
gcloud functions deploy chatbot-milesguo \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --trigger-http \
  --allow-unauthenticated \
  --memory 256Mi \
  --timeout 300s \
  --max-instances 10 \
  --set-env-vars "$ENV_VARS" \
  --verbosity=info

echo ""
echo "=== Deployment completed successfully! ==="

