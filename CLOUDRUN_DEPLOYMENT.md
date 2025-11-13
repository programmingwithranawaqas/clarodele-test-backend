# Cloud Run Deployment Guide

## Prerequisites

1. **Google Cloud Project**: `claro-dele-477408`
2. **Service Account**: `claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com`
3. **GCS Bucket**: `clarodele-mvp-content`
4. **GitHub Repository**: Connected to Google Cloud Build

## Authentication Setup

### For Local Development

Authenticate with your Gmail account:

```bash
# Login with your Gmail account (ranawaqas.pa@gmail.com)
gcloud auth login

# Set application default credentials
gcloud auth application-default login

# Set the project
gcloud config set project claro-dele-477408
```

### For Cloud Run (Production)

Cloud Run will automatically use the service account: `claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com`

No additional configuration needed - it's set in the deployment script.

## Deployment Methods

### Method 1: Automatic Deployment (GitHub → Cloud Run)

If your repository is connected to Cloud Run:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add audio migration features"
   git push origin main
   ```

2. **Cloud Run Auto-deploys**: The service will automatically redeploy when you push to the `main` branch.

### Method 2: Manual Deployment (Using Script)

```bash
# Make the script executable
chmod +x deploy.sh

# Deploy
./deploy.sh
```

### Method 3: Manual Deployment (gcloud command)

```bash
gcloud run deploy clarodele-test-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com \
  --set-env-vars "DATABASE_URL=postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require" \
  --set-env-vars "GCS_BUCKET_NAME=clarodele-mvp-content" \
  --memory 512Mi \
  --timeout 900 \
  --max-instances 10
```

## Using the Deployed Service

### Get Service URL

```bash
SERVICE_URL=$(gcloud run services describe clarodele-test-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

echo $SERVICE_URL
```

### Test the Service

```bash
# Health check
curl $SERVICE_URL/

# Ping
curl $SERVICE_URL/ping

# Test GCS access
curl $SERVICE_URL/test-gcs

# Check migration status
curl $SERVICE_URL/migration-status
```

### Run Migration

#### Test Mode (Dry Run)
```bash
# Migrate 5 rows in test mode (no database changes)
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=5&test_mode=true"
```

#### Real Migration
```bash
# Migrate 10 rows
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=10"

# Migrate all remaining rows
curl -X POST "$SERVICE_URL/migrate-audio-files"
```

### Monitor Progress

```bash
# Check status continuously
watch -n 5 "curl -s $SERVICE_URL/migration-status | jq"
```

## Cloud Run Configuration

### Environment Variables

These are automatically set during deployment:

- `DATABASE_URL`: PostgreSQL connection string
- `GCS_BUCKET_NAME`: Target GCS bucket name
- `PORT`: 8080 (Cloud Run default)

### Service Account Permissions

The service account `claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com` needs:

- **Storage Object Admin** on `clarodele-mvp-content` bucket
- Network access to Supabase database

### Resource Limits

- **Memory**: 512Mi
- **Timeout**: 900s (15 minutes)
- **Max Instances**: 10
- **Concurrency**: Default (80)

## Viewing Logs

```bash
# View recent logs
gcloud run services logs read clarodele-test-backend \
  --platform managed \
  --region us-central1 \
  --limit 50

# Follow logs in real-time
gcloud run services logs tail clarodele-test-backend \
  --platform managed \
  --region us-central1
```

## Migration Workflow on Cloud Run

### Step 1: Test the Deployment

```bash
# Set the service URL
SERVICE_URL=$(gcloud run services describe clarodele-test-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

# Test GCS access
curl $SERVICE_URL/test-gcs

# Expected response:
# {
#   "success": true,
#   "message": "Read and write access confirmed!",
#   "example_files": [...]
# }
```

### Step 2: Check Migration Status

```bash
curl $SERVICE_URL/migration-status

# Expected response:
# {
#   "success": true,
#   "column_exists": true,
#   "statistics": {
#     "total_rows": 100,
#     "rows_with_audio_url": 95,
#     "rows_with_bucket_url": 0,
#     "pending_migration": 95
#   }
# }
```

### Step 3: Run Test Migration

```bash
# Test with 2 rows, no database changes
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=2&test_mode=true"
```

### Step 4: Start Real Migration

```bash
# Migrate in batches of 10
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=10"

# Check progress
curl $SERVICE_URL/migration-status

# Continue until complete
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=10"
```

### Step 5: Monitor via Logs

```bash
# Watch logs in real-time
gcloud run services logs tail clarodele-test-backend \
  --platform managed \
  --region us-central1
```

## Troubleshooting

### Issue: Service Account Permissions

```bash
# Grant Storage Object Admin role
gcloud projects add-iam-policy-binding claro-dele-477408 \
  --member="serviceAccount:claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

### Issue: Database Connection

```bash
# Test database connection from Cloud Run
curl $SERVICE_URL/migration-status
```

If connection fails:
1. Check if Cloud Run IP range is whitelisted in Supabase
2. Verify DATABASE_URL environment variable is set correctly
3. Check Supabase logs for connection attempts

### Issue: Timeout

If migration times out (>15 minutes):

**Option A**: Reduce batch size
```bash
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=5"
```

**Option B**: Increase timeout (max 60 minutes for Cloud Run)
```bash
gcloud run services update clarodele-test-backend \
  --timeout 3600 \
  --region us-central1
```

### Issue: Memory Errors

```bash
# Increase memory allocation
gcloud run services update clarodele-test-backend \
  --memory 1Gi \
  --region us-central1
```

## Cost Optimization

### Run Migration in Batches

Instead of migrating all files at once, run in smaller batches to optimize cost:

```bash
# Migrate 20 rows at a time
for i in {1..5}; do
  echo "Batch $i"
  curl -X POST "$SERVICE_URL/migrate-audio-files?limit=20"
  sleep 5
done
```

### Schedule Migration

For large datasets, consider using Cloud Scheduler:

```bash
# Create a Cloud Scheduler job to run migration daily
gcloud scheduler jobs create http audio-migration-daily \
  --location us-central1 \
  --schedule "0 2 * * *" \
  --uri "$SERVICE_URL/migrate-audio-files?limit=50" \
  --http-method POST
```

## Security Best Practices

### 1. Restrict Access

If you want to require authentication:

```bash
gcloud run services update clarodele-test-backend \
  --no-allow-unauthenticated \
  --region us-central1
```

Then call with authentication:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $SERVICE_URL/migration-status
```

### 2. Use Secret Manager

For sensitive data like DATABASE_URL:

```bash
# Create secret
echo -n "postgresql://..." | gcloud secrets create database-url --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Update deployment to use secret
gcloud run services update clarodele-test-backend \
  --update-secrets DATABASE_URL=database-url:latest \
  --region us-central1
```

## Complete Migration Example

```bash
#!/bin/bash

# Complete migration script for Cloud Run

# Get service URL
SERVICE_URL=$(gcloud run services describe clarodele-test-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"

# Test connection
echo "Testing service..."
curl $SERVICE_URL/ping

# Check initial status
echo -e "\nInitial status:"
curl $SERVICE_URL/migration-status | jq

# Run test migration
echo -e "\nRunning test migration..."
curl -X POST "$SERVICE_URL/migrate-audio-files?limit=2&test_mode=true" | jq

# Run real migration in batches
BATCH_SIZE=10
TOTAL_BATCHES=10

for i in $(seq 1 $TOTAL_BATCHES); do
  echo -e "\n=== Batch $i/$TOTAL_BATCHES ==="
  
  # Run migration
  curl -X POST "$SERVICE_URL/migrate-audio-files?limit=$BATCH_SIZE" | jq
  
  # Check status
  echo "Current status:"
  curl $SERVICE_URL/migration-status | jq '.statistics'
  
  # Wait between batches
  sleep 5
done

echo -e "\n=== Migration Complete ==="
curl $SERVICE_URL/migration-status | jq
```

## Monitoring and Alerts

### Set Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Audio Migration Errors" \
  --condition-display-name="High error rate" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

### View Metrics

Visit: https://console.cloud.google.com/run/detail/us-central1/clarodele-test-backend/metrics

## Next Steps

1. **Deploy the service**: Run `./deploy.sh`
2. **Test GCS access**: `curl $SERVICE_URL/test-gcs`
3. **Check migration status**: `curl $SERVICE_URL/migration-status`
4. **Run test migration**: `curl -X POST "$SERVICE_URL/migrate-audio-files?limit=2&test_mode=true"`
5. **Start migration**: `curl -X POST "$SERVICE_URL/migrate-audio-files?limit=10"`
