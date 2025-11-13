# Audio File Migration: Google Drive to GCS

This project migrates audio files from Google Drive URLs to Google Cloud Storage (GCS) and updates the PostgreSQL database with the new bucket URLs.

## Overview

The migration process:
1. Reads rows from the `listening_tarea1_set` table
2. Downloads audio files from Google Drive URLs
3. Uploads them to the GCS bucket
4. Updates the `bucket_url` column with the new GCS URL

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Google Cloud Credentials

Ensure you have Google Cloud credentials configured:

```bash
# Set the path to your service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

### 3. Environment Variables (Optional)

You can override default settings with environment variables:

```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
export GCS_BUCKET_NAME="your-bucket-name"
```

## Usage

### Option 1: Standalone Script (Recommended)

The `migrate_audio.py` script is a standalone migration tool.

#### Test Mode (Recommended First)
Run a test migration on a few rows without saving to the database:

```bash
python migrate_audio.py --limit 5 --test-mode
```

#### Migrate a Limited Number of Rows
Process only 10 rows:

```bash
python migrate_audio.py --limit 10
```

#### Migrate All Rows
Process all pending rows:

```bash
python migrate_audio.py
```

### Option 2: FastAPI Endpoints

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

#### Check Migration Status

```bash
curl http://localhost:8000/migration-status
```

#### Run Migration via API

Test mode with limit:
```bash
curl -X POST "http://localhost:8000/migrate-audio-files?limit=5&test_mode=true"
```

Full migration:
```bash
curl -X POST "http://localhost:8000/migrate-audio-files"
```

## Migration Script Features

### Command Line Arguments

- `--limit N`: Process only N rows (useful for testing)
- `--test-mode`: Dry run - download and upload files but don't update database

### What the Script Does

1. **Column Creation**: Automatically creates the `bucket_url` column if it doesn't exist
2. **Statistics**: Shows before/after migration statistics
3. **Progress Tracking**: Displays progress for each row
4. **Error Handling**: Captures and reports errors for each failed row
5. **Cleanup**: Automatically removes temporary downloaded files

### Output Format

The script provides detailed output:

```
🎵 Audio Migration Script
============================================================
Database: listening_tarea1_set
GCS Bucket: clarodele-mvp-content
Limit: 5
Test Mode: True
============================================================

📊 Current Statistics:
  total_rows: 100
  rows_with_audio_url: 95
  rows_with_bucket_url: 0
  pending_migration: 95

🔄 Processing 5 rows...
⚠️  TEST MODE: Changes will NOT be saved to database

[1/5] Processing row ID 1...
  → Google Drive ID: 1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE
  → Downloading from Google Drive...
  → Downloaded 2,456,789 bytes
  → Uploading to GCS: listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3...
  → GCS URL: gs://clarodele-mvp-content/listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3
  ✓ Updated database

...

============================================================
📋 MIGRATION SUMMARY
============================================================
Total rows processed: 5
Successful: 5
Failed: 0
```

## Database Schema

The script automatically adds the `bucket_url` column to your table:

```sql
ALTER TABLE listening_tarea1_set 
ADD COLUMN IF NOT EXISTS bucket_url TEXT;
```

### Table Structure

- `id`: Row identifier
- `audio_url`: Original Google Drive URL
- `bucket_url`: New GCS URL (added by migration)

## GCS URL Format

Files are stored with this naming pattern:
```
gs://clarodele-mvp-content/listening_tarea1/{google_drive_file_id}.mp3
```

Example:
```
gs://clarodele-mvp-content/listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3
```

## Troubleshooting

### Google Drive Download Issues

If you encounter issues downloading from Google Drive:

1. **Private Files**: Ensure files are shared publicly or with the service account
2. **Large Files**: The script handles Google Drive's virus scan confirmation
3. **Rate Limits**: Add delays between requests if needed

### GCS Upload Issues

1. **Permissions**: Ensure your service account has `Storage Object Admin` role
2. **Bucket Access**: Verify the bucket name is correct
3. **Quotas**: Check your GCS quotas if uploads fail

### Database Connection Issues

1. **URL Encoding**: The password in the connection string is URL-encoded (`%40` = `@`, `%2C` = `,`)
2. **SSL**: The connection requires SSL (`sslmode=require`)
3. **Firewall**: Ensure your IP is whitelisted in Supabase

## Security Best Practices

1. **Environment Variables**: Store sensitive credentials in environment variables
2. **Service Account**: Use a service account with minimal required permissions
3. **Database Access**: Restrict database access to specific IPs
4. **Bucket Permissions**: Consider making files private and using signed URLs

## Production Deployment

### Cloud Run Deployment

The included `Dockerfile` can be used to deploy to Cloud Run:

```bash
# Build the image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/audio-migration

# Deploy to Cloud Run
gcloud run deploy audio-migration \
  --image gcr.io/YOUR_PROJECT/audio-migration \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DATABASE_URL \
  --set-env-vars GCS_BUCKET_NAME=$GCS_BUCKET_NAME
```

### Running as a Batch Job

For large migrations, consider running as a batch job:

```bash
# Run in background with nohup
nohup python migrate_audio.py > migration.log 2>&1 &

# Or use screen/tmux for long-running processes
screen -S migration
python migrate_audio.py
# Detach with Ctrl+A, D
```

## Monitoring

Monitor the migration progress:

```bash
# Watch the log file
tail -f migration.log

# Check current status
python -c "
from migrate_audio import get_db_connection, get_migration_stats
conn = get_db_connection()
stats = get_migration_stats(conn)
print(stats)
conn.close()
"
```

## API Endpoints

When running as FastAPI server:

### GET /migration-status
Check current migration status and statistics.

### POST /migrate-audio-files
Start migration process.

Parameters:
- `limit` (optional): Number of rows to process
- `test_mode` (optional): If true, runs without saving to database

### GET /test-gcs
Test GCS bucket access permissions.

## Notes

- Files are downloaded temporarily and deleted after upload
- The script processes rows with `audio_url` but no `bucket_url`
- Already migrated rows are automatically skipped
- All operations are logged for troubleshooting
