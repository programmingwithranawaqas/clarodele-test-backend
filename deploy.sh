#!/bin/bash

# Deployment script for Google Cloud Run
# Usage: ./deploy.sh

set -e

# Configuration
PROJECT_ID="claro-dele-477408"
SERVICE_NAME="clarodele-test-backend"
REGION="us-central1"
SERVICE_ACCOUNT="claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com"

# Database URL (URL-encoded)
DATABASE_URL="postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require"

# GCS Bucket
GCS_BUCKET_NAME="clarodele-mvp-content"

echo "🚀 Deploying Audio Migration Backend to Cloud Run"
echo "=================================================="
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"
echo "=================================================="
echo ""

# Set the project
echo "📌 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build and deploy
echo "🏗️  Building and deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars "DATABASE_URL=$DATABASE_URL" \
  --set-env-vars "GCS_BUCKET_NAME=$GCS_BUCKET_NAME" \
  --memory 512Mi \
  --timeout 900 \
  --max-instances 10

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Service URL:"
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'

echo ""
echo "🔗 Available endpoints:"
echo "  GET  / - Health check"
echo "  GET  /ping - Ping endpoint"
echo "  GET  /test-gcs - Test GCS access"
echo "  GET  /migration-status - Check migration status"
echo "  POST /migrate-audio-files - Start migration"
echo ""
echo "💡 Example usage:"
echo "  SERVICE_URL=\$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')"
echo "  curl \$SERVICE_URL/migration-status"
echo "  curl -X POST \"\$SERVICE_URL/migrate-audio-files?limit=5&test_mode=true\""
echo ""
