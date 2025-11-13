#!/usr/bin/env python3
"""
Audio Migration Script: Google Drive to Google Cloud Storage

This script migrates audio files from Google Drive URLs to GCS bucket
and updates the PostgreSQL database with the new bucket URLs.

Usage:
    python migrate_audio.py --limit 10 --test-mode  # Test with 10 rows
    python migrate_audio.py                         # Migrate all rows
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from google.cloud import storage
import requests
import os
import tempfile
import re
import argparse
from typing import Optional


# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require"
)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "clarodele-mvp-content")
TABLE_NAME = "listening_tarea1_set"
AUDIO_URL_COLUMN = "audio_url"
BUCKET_URL_COLUMN = "bucket_url"


def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(DATABASE_URL)


def extract_google_drive_id(url: str) -> Optional[str]:
    """Extract file ID from Google Drive URL"""
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/open\?id=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def download_from_google_drive(file_id: str, destination: str) -> bool:
    """Download file from Google Drive using direct download link"""
    try:
        # Google Drive direct download URL
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        session = requests.Session()
        response = session.get(url, stream=True)
        
        # Handle large files with confirmation token
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                params = {'export': 'download', 'id': file_id, 'confirm': value}
                response = session.get(url, params=params, stream=True)
                break
        
        # Check if response is valid
        if response.status_code != 200:
            print(f"Failed to download: HTTP {response.status_code}")
            return False
        
        # Save file
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(32768):
                if chunk:
                    f.write(chunk)
        
        # Verify file was downloaded
        if os.path.getsize(destination) == 0:
            print("Downloaded file is empty")
            return False
        
        return True
    except Exception as e:
        print(f"Error downloading from Google Drive: {str(e)}")
        return False


def upload_to_gcs(local_file_path: str, destination_blob_name: str) -> Optional[str]:
    """Upload file to Google Cloud Storage and return GCS URL"""
    try:
        # Initialize client - will use Application Default Credentials
        # For local: run `gcloud auth application-default login`
        # For production: uses GOOGLE_APPLICATION_CREDENTIALS
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        
        # Set content type for audio files
        content_type = "audio/mpeg"
        if destination_blob_name.endswith('.mp3'):
            content_type = "audio/mpeg"
        elif destination_blob_name.endswith('.wav'):
            content_type = "audio/wav"
        
        # Upload file
        blob.upload_from_filename(local_file_path, content_type=content_type)
        
        # Optionally make the blob publicly accessible
        # blob.make_public()
        
        # Return the GCS URL
        gcs_url = f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        
        # Or return public HTTPS URL if blob is public:
        # public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{destination_blob_name}"
        
        return gcs_url
    except Exception as e:
        print(f"Error uploading to GCS: {str(e)}")
        return None


def update_bucket_url(conn, row_id: int, bucket_url: str):
    """Update the bucket_url column for a specific row"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"UPDATE {TABLE_NAME} SET {BUCKET_URL_COLUMN} = %s WHERE id = %s",
            (bucket_url, row_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


def ensure_column_exists(conn):
    """Ensure the bucket_url column exists in the table"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            ALTER TABLE {TABLE_NAME} 
            ADD COLUMN IF NOT EXISTS {BUCKET_URL_COLUMN} TEXT;
        """)
        conn.commit()
        print(f"✓ Ensured column '{BUCKET_URL_COLUMN}' exists in table '{TABLE_NAME}'")
    except Exception as e:
        print(f"Note: {e}")
        conn.rollback()
    finally:
        cursor.close()


def get_migration_stats(conn):
    """Get current migration statistics"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT({AUDIO_URL_COLUMN}) as rows_with_audio_url,
                COUNT({BUCKET_URL_COLUMN}) as rows_with_bucket_url,
                COUNT(CASE WHEN {AUDIO_URL_COLUMN} IS NOT NULL 
                      AND ({BUCKET_URL_COLUMN} IS NULL OR {BUCKET_URL_COLUMN} = '') 
                      THEN 1 END) as pending_migration
            FROM {TABLE_NAME};
        """)
        return dict(cursor.fetchone())
    finally:
        cursor.close()


def migrate_audio_files(limit: Optional[int] = None, test_mode: bool = False):
    """
    Main migration function
    
    Args:
        limit: Number of rows to process (None = all rows)
        test_mode: If True, don't commit changes to database
    """
    conn = None
    results = {
        "total_rows": 0,
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()
        
        # Ensure bucket_url column exists
        ensure_column_exists(conn)
        
        # Show current stats
        print("\n📊 Current Statistics:")
        stats = get_migration_stats(conn)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Fetch rows that need migration
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = f"""
            SELECT id, {AUDIO_URL_COLUMN}, {BUCKET_URL_COLUMN}
            FROM {TABLE_NAME} 
            WHERE {AUDIO_URL_COLUMN} IS NOT NULL 
            AND ({BUCKET_URL_COLUMN} IS NULL OR {BUCKET_URL_COLUMN} = '')
            ORDER BY id
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        results["total_rows"] = len(rows)
        
        print(f"\n🔄 Processing {len(rows)} rows...")
        if test_mode:
            print("⚠️  TEST MODE: Changes will NOT be saved to database")
        print()
        
        # Process each row
        for idx, row in enumerate(rows, 1):
            row_id = row['id']
            audio_url = row[AUDIO_URL_COLUMN]
            
            print(f"[{idx}/{len(rows)}] Processing row ID {row_id}...")
            
            try:
                # Extract Google Drive file ID
                file_id = extract_google_drive_id(audio_url)
                if not file_id:
                    print(f"  ✗ Could not extract Google Drive file ID from: {audio_url}")
                    results["failed"] += 1
                    results["errors"].append({
                        "row_id": row_id,
                        "error": "Could not extract Google Drive file ID",
                        "url": audio_url
                    })
                    continue
                
                print(f"  → Google Drive ID: {file_id}")
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file_path = tmp_file.name
                
                try:
                    # Download from Google Drive
                    print(f"  → Downloading from Google Drive...")
                    if not download_from_google_drive(file_id, tmp_file_path):
                        print(f"  ✗ Failed to download from Google Drive")
                        results["failed"] += 1
                        results["errors"].append({
                            "row_id": row_id,
                            "error": "Failed to download from Google Drive",
                            "file_id": file_id
                        })
                        continue
                    
                    file_size = os.path.getsize(tmp_file_path)
                    print(f"  → Downloaded {file_size:,} bytes")
                    
                    # Upload to GCS with organized path
                    destination_blob_name = f"listening_tarea1/{file_id}.mp3"
                    print(f"  → Uploading to GCS: {destination_blob_name}...")
                    bucket_url = upload_to_gcs(tmp_file_path, destination_blob_name)
                    
                    if not bucket_url:
                        print(f"  ✗ Failed to upload to GCS")
                        results["failed"] += 1
                        results["errors"].append({
                            "row_id": row_id,
                            "error": "Failed to upload to GCS",
                            "file_id": file_id
                        })
                        continue
                    
                    print(f"  → GCS URL: {bucket_url}")
                    
                    # Update database
                    if not test_mode:
                        update_bucket_url(conn, row_id, bucket_url)
                        print(f"  ✓ Updated database")
                    else:
                        print(f"  ⊘ [TEST MODE] Would update database")
                    
                    results["successful"] += 1
                    print()
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                results["failed"] += 1
                results["errors"].append({
                    "row_id": row_id,
                    "error": str(e),
                    "url": audio_url
                })
                print()
        
        cursor.close()
        
        # Print summary
        print("\n" + "="*60)
        print("📋 MIGRATION SUMMARY")
        print("="*60)
        print(f"Total rows processed: {results['total_rows']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"  Row {error['row_id']}: {error['error']}")
            if len(results['errors']) > 5:
                print(f"  ... and {len(results['errors']) - 5} more")
        
        # Show updated stats
        if not test_mode and results['successful'] > 0:
            print("\n📊 Updated Statistics:")
            stats = get_migration_stats(conn)
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("\n✓ Database connection closed")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate audio files from Google Drive to GCS"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rows to process (default: all)"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (don't save to database)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("🎵 Audio Migration Script")
    print("="*60)
    print(f"Database: {TABLE_NAME}")
    print(f"GCS Bucket: {GCS_BUCKET_NAME}")
    print(f"Limit: {args.limit if args.limit else 'No limit (all rows)'}")
    print(f"Test Mode: {args.test_mode}")
    print("="*60)
    print()
    
    migrate_audio_files(limit=args.limit, test_mode=args.test_mode)


if __name__ == "__main__":
    main()
