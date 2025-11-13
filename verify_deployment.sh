#!/bin/bash

# Quick deployment verification script
# Usage: ./verify_deployment.sh

set -e

PROJECT_ID="claro-dele-477408"
SERVICE_NAME="clarodele-test-backend"
REGION="us-central1"

echo "🔍 Verifying Cloud Run Deployment"
echo "=================================="
echo ""

# Set project
gcloud config set project $PROJECT_ID 2>/dev/null

# Get service URL
echo "📡 Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)' 2>/dev/null)

if [ -z "$SERVICE_URL" ]; then
  echo "❌ Service not found or not deployed yet"
  echo ""
  echo "To deploy, run: ./deploy.sh"
  exit 1
fi

echo "✓ Service URL: $SERVICE_URL"
echo ""

# Test endpoints
echo "🧪 Testing Endpoints..."
echo "------------------------"

# Health check
echo -n "1. Health Check (GET /): "
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" $SERVICE_URL/)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ OK"
else
  echo "✗ FAILED (HTTP $HTTP_CODE)"
fi

# Ping
echo -n "2. Ping (GET /ping): "
PING_RESPONSE=$(curl -s -w "\n%{http_code}" $SERVICE_URL/ping)
HTTP_CODE=$(echo "$PING_RESPONSE" | tail -n 1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ OK"
else
  echo "✗ FAILED (HTTP $HTTP_CODE)"
fi

# GCS Test
echo -n "3. GCS Access (GET /test-gcs): "
GCS_RESPONSE=$(curl -s -w "\n%{http_code}" $SERVICE_URL/test-gcs)
HTTP_CODE=$(echo "$GCS_RESPONSE" | tail -n 1)
BODY=$(echo "$GCS_RESPONSE" | head -n -1)
if [ "$HTTP_CODE" = "200" ] && echo "$BODY" | grep -q '"success":true'; then
  echo "✓ OK"
else
  echo "✗ FAILED (HTTP $HTTP_CODE)"
  echo "   Response: $BODY"
fi

# Migration Status
echo -n "4. Migration Status (GET /migration-status): "
STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" $SERVICE_URL/migration-status)
HTTP_CODE=$(echo "$STATUS_RESPONSE" | tail -n 1)
BODY=$(echo "$STATUS_RESPONSE" | head -n -1)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ OK"
  # Parse and display statistics if available
  if command -v jq &> /dev/null; then
    echo ""
    echo "   📊 Current Statistics:"
    echo "$BODY" | jq -r '.statistics | to_entries[] | "      \(.key): \(.value)"' 2>/dev/null || true
  fi
else
  echo "✗ FAILED (HTTP $HTTP_CODE)"
  echo "   Response: $BODY"
fi

echo ""
echo "=================================="
echo "✅ Verification Complete!"
echo ""
echo "📋 Service Information:"
echo "   URL: $SERVICE_URL"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""
echo "💡 Next Steps:"
echo "   - Test migration: curl -X POST \"$SERVICE_URL/migrate-audio-files?limit=2&test_mode=true\""
echo "   - Start migration: curl -X POST \"$SERVICE_URL/migrate-audio-files?limit=10\""
echo "   - View logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
