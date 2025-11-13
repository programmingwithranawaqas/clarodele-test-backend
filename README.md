# Audio Migration Project - Overview

## 🚀 Deployment Options

This project can be run in two ways:

### Option 1: Google Cloud Run (Recommended for Production) ⭐

The project is connected to your GitHub repository and automatically deploys to Google Cloud Run.

**Quick Deploy:**
```bash
# Push to GitHub - auto-deploys to Cloud Run
git add .
git commit -m "Deploy audio migration"
git push origin main

# Or deploy manually
./deploy.sh

# Verify deployment
./verify_deployment.sh
```

📖 **See [CLOUDRUN_DEPLOYMENT.md](CLOUDRUN_DEPLOYMENT.md) for complete Cloud Run guide**

### Option 2: Local Development

For local testing and development:

```bash
# Authenticate with your Gmail
gcloud auth application-default login

# Run locally
python migrate_audio.py --limit 5 --test-mode
```

📖 **See [QUICKSTART.md](QUICKSTART.md) for local development guide**

---

## 📁 Project Files

### Core Files

1. **`migrate_audio.py`** ⭐ (Main Migration Script)
   - Standalone script for migrating audio files
   - Downloads from Google Drive
   - Uploads to GCS bucket
   - Updates PostgreSQL database
   - **Usage**: `python migrate_audio.py --limit 5 --test-mode`

2. **`main.py`** (FastAPI Application)
   - FastAPI server with migration endpoints
   - Includes GCS test endpoint
   - API-based migration control
   - **Usage**: `uvicorn main:app --reload`

3. **`requirements.txt`**
   - Python dependencies
   - Includes: FastAPI, psycopg2, google-cloud-storage, requests

### Helper Scripts

4. **`check_database.py`** 🔍
   - Verifies database connection
   - Shows table structure
   - Displays migration statistics
   - **Usage**: `python check_database.py`

5. **`test_parsing.py`**
   - Tests Google Drive URL parsing
   - Validates file ID extraction
   - **Usage**: `python test_parsing.py`

### Documentation

6. **`QUICKSTART.md`** 📖
   - Step-by-step instructions
   - Quick reference guide
   - Troubleshooting tips

7. **`MIGRATION_README.md`** 📚
   - Comprehensive documentation
   - Detailed explanations
   - Production deployment guide

8. **`Dockerfile`**
   - Container configuration for Cloud Run
   - Production deployment ready

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Google Cloud Credentials
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Step 3: Verify Setup
```bash
python check_database.py
```

### Step 4: Test Migration
```bash
python migrate_audio.py --limit 2 --test-mode
```

### Step 5: Run Migration
```bash
python migrate_audio.py --limit 10
```

## 📊 What It Does

```
┌─────────────────────┐
│  PostgreSQL Table   │
│ listening_tarea1_set│
│                     │
│ - id                │
│ - audio_url ───────┼─► Google Drive URL
│ - bucket_url (new)  │
└─────────────────────┘
           │
           ▼
    [Migration Script]
           │
           ├─► Download from Google Drive
           │
           ├─► Upload to GCS Bucket
           │   (clarodele-mvp-content)
           │
           └─► Update bucket_url in database
```

## 🎯 Migration Flow

1. **Read** rows from `listening_tarea1_set` table
2. **Extract** Google Drive file ID from `audio_url`
3. **Download** file from Google Drive
4. **Upload** to GCS bucket: `gs://clarodele-mvp-content/listening_tarea1/{file_id}.mp3`
5. **Update** `bucket_url` column with new GCS URL
6. **Clean up** temporary files

## 🔧 Configuration

### Environment Variables

```bash
# Database (default provided)
export DATABASE_URL="postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require"

# GCS Bucket (default: clarodele-mvp-content)
export GCS_BUCKET_NAME="your-bucket-name"

# Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## 📝 Sample URLs

### Input (Google Drive)
```
https://drive.google.com/file/d/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE/view?usp=drivesdk
```

### Output (GCS)
```
gs://clarodele-mvp-content/listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3
```

## ✅ Features

- ✓ Automatic column creation (`bucket_url`)
- ✓ Test mode for dry runs
- ✓ Progress tracking and statistics
- ✓ Error handling and reporting
- ✓ Automatic cleanup of temporary files
- ✓ Batch processing with limits
- ✓ Skip already migrated rows
- ✓ Detailed logging

## 🛠️ Tools Comparison

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `migrate_audio.py` | Standalone migration | ⭐ **Primary tool** for migration |
| `main.py` (FastAPI) | API server | When you need API endpoints |
| `check_database.py` | Database verification | Before starting migration |
| `test_parsing.py` | URL validation | To verify URL format |

## 📋 Recommended Workflow

```bash
# 1. Verify database connection
python check_database.py

# 2. Test URL parsing
python test_parsing.py

# 3. Run test migration (2 rows, no database changes)
python migrate_audio.py --limit 2 --test-mode

# 4. If test successful, migrate in small batches
python migrate_audio.py --limit 10

# 5. Continue with larger batches or all at once
python migrate_audio.py --limit 50
# or
python migrate_audio.py  # All remaining rows
```

## ⚠️ Important Notes

1. **Always test first** with `--test-mode`
2. **Start small** with `--limit 10`
3. **Google Cloud credentials** must be configured
4. **Google Drive files** should be publicly accessible
5. **Database backups** recommended before migration

## 🔍 Monitoring

```bash
# Check migration progress
python check_database.py

# Or query directly
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as total, COUNT(bucket_url) as migrated FROM listening_tarea1_set WHERE audio_url IS NOT NULL;')
result = cursor.fetchone()
print(f'Progress: {result[1]}/{result[0]} ({result[1]/result[0]*100:.1f}%)')
conn.close()
"
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check if IP is whitelisted in Supabase |
| GCS upload failed | Verify service account has Storage Object Admin role |
| Google Drive download failed | Ensure files are publicly accessible |
| Column doesn't exist | Script auto-creates it on first run |

## 📚 Documentation

- **Quick Start**: See `QUICKSTART.md`
- **Full Documentation**: See `MIGRATION_README.md`
- **API Reference**: Run `uvicorn main:app --reload` and visit `/docs`

## 🎓 Example Output

```
🎵 Audio Migration Script
============================================================
Database: listening_tarea1_set
GCS Bucket: clarodele-mvp-content
Limit: 5
Test Mode: False
============================================================

✓ Ensured column 'bucket_url' exists

📊 Current Statistics:
  total_rows: 100
  rows_with_audio_url: 95
  rows_with_bucket_url: 0
  pending_migration: 95

🔄 Processing 5 rows...

[1/5] Processing row ID 1...
  → Google Drive ID: 1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE
  → Downloading from Google Drive...
  → Downloaded 2,456,789 bytes
  → Uploading to GCS: listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3
  → GCS URL: gs://clarodele-mvp-content/listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3
  ✓ Updated database

============================================================
📋 MIGRATION SUMMARY
============================================================
Total rows processed: 5
Successful: 5
Failed: 0

📊 Updated Statistics:
  total_rows: 100
  rows_with_audio_url: 95
  rows_with_bucket_url: 5
  pending_migration: 90
```

## 🚀 Next Steps

1. **Test the setup**: Run `python check_database.py`
2. **Verify credentials**: Ensure Google Cloud service account is configured
3. **Test migration**: Run with `--test-mode` first
4. **Start migration**: Begin with small batches
5. **Monitor progress**: Use `check_database.py` to track status

## 💡 Pro Tips

- Use `--limit` to process in batches
- Always use `--test-mode` first
- Monitor disk space for temporary files
- Check GCS bucket after migration to verify files
- Keep migration logs for troubleshooting

---

**Ready to start?** Run `python check_database.py` to verify your setup!
