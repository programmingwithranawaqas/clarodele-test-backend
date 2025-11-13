# Quick Start Guide: Audio Migration

## Prerequisites

1. **Google Cloud Service Account** with access to the GCS bucket
2. **Service Account Key JSON** file downloaded
3. **Python 3.8+** installed

## Step-by-Step Instructions

### 1. Set Up Environment

```bash
# Navigate to the project directory
cd "/Users/Shared/Files From e.localized/Drive E/AIC Expert/clarodele-test-backend"

# Install dependencies
pip install -r requirements.txt

# Set Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

### 2. Test URL Parsing (Optional)

```bash
python test_parsing.py
```

This verifies that Google Drive URLs are parsed correctly.

### 3. Run Test Migration

**IMPORTANT**: Always test first!

```bash
# Test with 2 rows, no database changes
python migrate_audio.py --limit 2 --test-mode
```

Expected output:
```
🎵 Audio Migration Script
============================================================
Database: listening_tarea1_set
GCS Bucket: clarodele-mvp-content
Limit: 2
Test Mode: True
============================================================

✓ Ensured column 'bucket_url' exists in table 'listening_tarea1_set'

📊 Current Statistics:
  total_rows: 100
  rows_with_audio_url: 95
  rows_with_bucket_url: 0
  pending_migration: 95

🔄 Processing 2 rows...
⚠️  TEST MODE: Changes will NOT be saved to database

[1/2] Processing row ID 1...
  → Google Drive ID: 1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE
  → Downloading from Google Drive...
  → Downloaded 2,456,789 bytes
  → Uploading to GCS: listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3...
  → GCS URL: gs://clarodele-mvp-content/listening_tarea1/1NsguVph4o3CEeYr16Ov4aT_8mHCJqvRE.mp3
  ⊘ [TEST MODE] Would update database

============================================================
📋 MIGRATION SUMMARY
============================================================
Total rows processed: 2
Successful: 2
Failed: 0
```

### 4. Run Real Migration

Once test is successful:

```bash
# Option A: Migrate 10 rows at a time (recommended)
python migrate_audio.py --limit 10

# Option B: Migrate all rows
python migrate_audio.py
```

### 5. Monitor Progress

Check the migration status:

```bash
# Run this in another terminal
python -c "
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect('postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require')
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute('''
    SELECT 
        COUNT(*) as total,
        COUNT(bucket_url) as migrated,
        COUNT(*) - COUNT(bucket_url) as remaining
    FROM listening_tarea1_set
    WHERE audio_url IS NOT NULL;
''')

stats = cursor.fetchone()
print(f\"Total: {stats['total']}\")
print(f\"Migrated: {stats['migrated']}\")
print(f\"Remaining: {stats['remaining']}\")
print(f\"Progress: {stats['migrated']/stats['total']*100:.1f}%\")

cursor.close()
conn.close()
"
```

## Troubleshooting

### Issue: "Could not extract Google Drive file ID"

**Solution**: Check if the URL format is correct. The URL should look like:
```
https://drive.google.com/file/d/FILE_ID/view?usp=drivesdk
```

### Issue: "Failed to download from Google Drive"

**Solutions**:
1. Ensure files are shared publicly or with service account email
2. Check if file still exists on Google Drive
3. Verify internet connection

### Issue: "Failed to upload to GCS"

**Solutions**:
1. Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
2. Check service account has "Storage Object Admin" role
3. Verify bucket name is correct: `clarodele-mvp-content`

### Issue: Database connection fails

**Solutions**:
1. Check if IP is whitelisted in Supabase
2. Verify DATABASE_URL is correct
3. Test connection:
```bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require'); print('Connected!'); conn.close()"
```

## Best Practices

1. **Always test first**: Use `--test-mode` before real migration
2. **Start small**: Use `--limit 10` for first real migration
3. **Monitor**: Watch the output for any errors
4. **Incremental**: Migrate in batches (10-50 rows) rather than all at once
5. **Backup**: Ensure you have a database backup before starting

## Verify Migration

After migration, verify a few files:

```bash
# Check a random row in database
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require')
cursor = conn.cursor()
cursor.execute('SELECT id, audio_url, bucket_url FROM listening_tarea1_set WHERE bucket_url IS NOT NULL LIMIT 5;')
rows = cursor.fetchall()
for row in rows:
    print(f'ID: {row[0]}')
    print(f'  Audio URL: {row[1][:60]}...')
    print(f'  Bucket URL: {row[2]}')
    print()
cursor.close()
conn.close()
"
```

## Getting Help

If you encounter issues:

1. Check the error messages in the terminal output
2. Review the MIGRATION_README.md for detailed documentation
3. Verify all prerequisites are met
4. Check Google Cloud and Supabase dashboards for permissions

## Summary Commands

```bash
# Quick test
python migrate_audio.py --limit 2 --test-mode

# Incremental migration
python migrate_audio.py --limit 10

# Full migration
python migrate_audio.py
```
