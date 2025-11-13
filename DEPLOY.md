# 🚀 Automated Deployment Guide

## Quick Deploy (3 Steps)

### Step 1: Push to GitHub

```bash
cd "/Users/Shared/Files From e.localized/Drive E/AIC Expert/clarodele-test-backend"

git add .
git commit -m "Add automated audio migration system"
git push origin main
```

### Step 2: Wait for Auto-Deploy

Google Cloud Run will automatically detect the push and deploy your service.

- Go to: https://console.cloud.google.com/run
- Select your service: `clarodele-test-backend`
- Watch the deployment progress (usually takes 2-3 minutes)

### Step 3: Open the URL

Once deployed, click on the service URL or visit:
```
https://clarodele-test-backend-XXXXXXXXXX-uc.a.run.app
```

**That's it!** You'll see a web interface with buttons to:
- 📊 Check Migration Status
- 🚀 Start Auto-Migration

---

## What Happens When You Visit the URL?

1. **Homepage loads** - Shows a nice web interface
2. **Status automatically loads** - Shows current migration statistics
3. **Click "Start Auto-Migration"** - Migrates ALL files automatically
4. **Watch progress** - See real-time results in the browser

---

## One-Click Migration

Just visit this endpoint in your browser:

```
https://your-service-url.run.app/start-migration
```

This will:
- ✅ Automatically migrate ALL pending files
- ✅ Process in batches of 10
- ✅ Skip already migrated files
- ✅ Return complete statistics
- ✅ Safe to run multiple times

---

## Environment Variables (Already Set in deploy.sh)

These are automatically configured when you deploy:

```bash
DATABASE_URL=postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require
GCS_BUCKET_NAME=clarodele-mvp-content
```

The service account `claro-dele-backend@claro-dele-477408.iam.gserviceaccount.com` is automatically used.

---

## Manual Deployment (If Needed)

If automatic deployment doesn't work:

```bash
./deploy.sh
```

Or use the gcloud command:

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
  --timeout 900
```

---

## Testing After Deployment

### Option 1: Use the Web Interface (Easiest)

1. Open your Cloud Run service URL in a browser
2. Click "Check Migration Status"
3. Click "Start Auto-Migration"
4. Watch the results!

### Option 2: Use curl

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe clarodele-test-backend \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)')

# Check status
curl $SERVICE_URL/migration-status

# Start migration
curl $SERVICE_URL/start-migration
```

---

## How the Auto-Migration Works

```
📱 You visit /start-migration
    ↓
🔍 System checks for pending files
    ↓
📥 Downloads from Google Drive (batch of 10)
    ↓
📤 Uploads to GCS bucket
    ↓
💾 Updates database with new URLs
    ↓
🔄 Repeats until all files are migrated
    ↓
✅ Returns complete statistics
```

---

## Monitoring

### View Logs

```bash
# Real-time logs
gcloud run services logs tail clarodele-test-backend \
  --platform managed \
  --region us-central1

# Recent logs
gcloud run services logs read clarodele-test-backend \
  --platform managed \
  --region us-central1 \
  --limit 100
```

### Check Service Status

```bash
gcloud run services describe clarodele-test-backend \
  --platform managed \
  --region us-central1
```

---

## Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface (open in browser) |
| `/start-migration` | GET | ⭐ Auto-migrate all files |
| `/migration-status` | GET | Check current status |
| `/migrate-audio-files` | POST | Migrate with options (limit, test_mode) |
| `/test-gcs` | GET | Test GCS access |
| `/ping` | GET | Health check |

---

## Troubleshooting

### Issue: Service not deploying

```bash
# Check build logs
gcloud builds list --limit 5

# View specific build
gcloud builds log BUILD_ID
```

### Issue: Migration fails

1. Check logs: `gcloud run services logs tail clarodele-test-backend --region us-central1`
2. Test GCS access: Visit `/test-gcs` endpoint
3. Check database: Visit `/migration-status` endpoint

### Issue: Timeout errors

If migration times out, the system automatically processes in batches. Just run `/start-migration` again - it will continue from where it left off.

---

## Cost Optimization

The service is configured for cost efficiency:

- **Memory**: 512Mi (enough for audio processing)
- **Timeout**: 15 minutes (handles large batches)
- **Auto-scaling**: Scales to zero when not in use
- **Batching**: Processes 10 files at a time

**Estimated cost**: ~$0.01 per 100 files migrated

---

## Security

✅ **Service Account**: Uses dedicated service account  
✅ **Database**: SSL-encrypted connection  
✅ **Storage**: Private GCS bucket access  
✅ **Temporary Files**: Auto-cleaned after processing  

---

## Next Steps After Deployment

1. **Verify deployment**: `./verify_deployment.sh`
2. **Open the URL** in your browser
3. **Click "Check Migration Status"** to see current state
4. **Click "Start Auto-Migration"** to migrate all files
5. **Monitor progress** in the web interface or logs

---

## Summary

**Before:**
- Complex manual process
- Multiple commands needed
- Error-prone

**Now:**
1. Push to GitHub
2. Visit the URL
3. Click "Start Auto-Migration"
4. Done! ✨

Everything is automated and runs in the cloud!
