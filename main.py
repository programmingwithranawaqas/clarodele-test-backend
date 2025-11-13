from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google.cloud import storage
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import os
import tempfile
from typing import Optional
from urllib.parse import unquote
import re

app = FastAPI(title="Audio Migration API", version="1.0.0")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require"
)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ycnqrnacilcwqqgelaod.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # You'll need to provide this
BUCKET_NAME = os.getenv("BUCKET_NAME", "audio-files")  # Default bucket name

# GCS Bucket name
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "clarodele-mvp-content")


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
        
        # Save file
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(32768):
                if chunk:
                    f.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading from Google Drive: {str(e)}")
        return False


def upload_to_gcs(local_file_path: str, destination_blob_name: str) -> Optional[str]:
    """Upload file to Google Cloud Storage and return public URL"""
    try:
        # Initialize client - will use Application Default Credentials
        # For local: run `gcloud auth application-default login`
        # For production: uses GOOGLE_APPLICATION_CREDENTIALS
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        
        # Upload file
        blob.upload_from_filename(local_file_path)
        
        # Make the blob publicly accessible (optional)
        # blob.make_public()
        
        # Return the public URL
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        # Or return public URL: return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCS: {str(e)}")
        return None


def update_bucket_url(conn, row_id: int, bucket_url: str):
    """Update the bucket_url column for a specific row"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE listening_tarea1_set SET bucket_url = %s WHERE tarea1_set_id = %s",
            (bucket_url, row_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Root endpoint with HTML interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audio Migration - Cloud Run</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }
            .status-box {
                background: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }
            .button {
                display: inline-block;
                padding: 12px 24px;
                margin: 10px 5px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background 0.3s;
            }
            .button:hover {
                background: #45a049;
            }
            .button.secondary {
                background: #2196F3;
            }
            .button.secondary:hover {
                background: #0b7dda;
            }
            .endpoint {
                background: #f9f9f9;
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
                font-family: monospace;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                background: #f9f9f9;
                border-radius: 5px;
                white-space: pre-wrap;
                font-family: monospace;
                font-size: 12px;
                max-height: 400px;
                overflow-y: auto;
            }
            .success { border-left: 4px solid #4CAF50; }
            .error { border-left: 4px solid #f44336; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Audio Migration System</h1>
            
            <div class="status-box">
                <strong>📊 Status:</strong> System Ready<br>
                <strong>🗄️ Database:</strong> Supabase PostgreSQL<br>
                <strong>☁️ Storage:</strong> Google Cloud Storage<br>
                <strong>📦 Bucket:</strong> clarodele-mvp-content
            </div>

            <h2>Quick Actions</h2>
            
            <a href="#" class="button" onclick="checkStatus(); return false;">
                📊 Check Migration Status
            </a>
            
            <a href="#" class="button secondary" onclick="startMigration(); return false;">
                🚀 Start Auto-Migration
            </a>

            <h2>Available Endpoints</h2>
            
            <div class="endpoint">
                <strong>GET</strong> /migration-status - Check current migration status
            </div>
            <div class="endpoint">
                <strong>GET</strong> /start-migration - ⭐ Start automatic migration of all files
            </div>
            <div class="endpoint">
                <strong>POST</strong> /migrate-audio-files?limit=10 - Migrate specific number of files
            </div>
            <div class="endpoint">
                <strong>GET</strong> /test-gcs - Test GCS bucket access
            </div>

            <div class="loading" id="loading">
                <p>⏳ Processing... Please wait...</p>
            </div>

            <div id="result"></div>
        </div>

        <script>
            function showLoading() {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').innerHTML = '';
            }

            function hideLoading() {
                document.getElementById('loading').style.display = 'none';
            }

            function showResult(data, isError = false) {
                hideLoading();
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result ' + (isError ? 'error' : 'success');
                resultDiv.innerHTML = JSON.stringify(data, null, 2);
            }

            async function checkStatus() {
                showLoading();
                try {
                    const response = await fetch('/migration-status');
                    const data = await response.json();
                    showResult(data);
                } catch (error) {
                    showResult({error: error.message}, true);
                }
            }

            async function startMigration() {
                if (!confirm('Start automatic migration of all pending files?\\n\\nThis will migrate all files in batches of 10.')) {
                    return;
                }
                
                showLoading();
                try {
                    const response = await fetch('/start-migration');
                    const data = await response.json();
                    showResult(data);
                } catch (error) {
                    showResult({error: error.message}, true);
                }
            }

            // Auto-load status on page load
            window.onload = function() {
                checkStatus();
            };
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/ping")
def ping():
    return {"status": "ok"}

# ----------------------------------------------------------
# 🚀 Test Endpoint to Check GCS Permissions
# ----------------------------------------------------------
@app.get("/test-gcs")
def test_gcs_access():
    """
    Test read/write permissions on the client's GCS bucket
    """
    try:
        client = storage.Client()
        bucket_name = "clarodele-mvp-content"  # Client's bucket
        bucket = client.bucket(bucket_name)

        # Try reading first 2 files
        blobs = list(bucket.list_blobs(max_results=2))
        blob_names = [b.name for b in blobs] if blobs else []

        # Try writing a small test file
        test_blob = bucket.blob("test_access_from_cloudrun.txt")
        test_blob.upload_from_string("✅ Cloud Run has access to this bucket.")

        return {
            "success": True,
            "message": "Read and write access confirmed!",
            "example_files": blob_names,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ----------------------------------------------------------
# 🔄 Migrate Audio Files from Google Drive to GCS
# ----------------------------------------------------------
@app.post("/migrate-audio-files")
async def migrate_audio_files(limit: Optional[int] = None, test_mode: bool = False):
    """
    Migrate audio files from Google Drive to GCS bucket
    
    Args:
        limit: Number of rows to process (None = all rows)
        test_mode: If True, only process rows without committing to database
    
    Returns:
        Migration results with success/failure counts
    """
    conn = None
    results = {
        "total_rows": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First, check if bucket_url column exists, if not create it
        try:
            cursor.execute("""
                ALTER TABLE listening_tarea1_set 
                ADD COLUMN IF NOT EXISTS bucket_url TEXT;
            """)
            conn.commit()
        except Exception as e:
            print(f"Column might already exist: {e}")
            conn.rollback()
        
        # Fetch rows that need migration
        query = """
            SELECT tarea1_set_id as id, audio_url, bucket_url 
            FROM listening_tarea1_set 
            WHERE audio_url IS NOT NULL 
            AND (bucket_url IS NULL OR bucket_url = '')
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        results["total_rows"] = len(rows)
        
        print(f"Found {len(rows)} rows to process")
        
        # Process each row
        for row in rows:
            row_id = row['id']
            audio_url = row['audio_url']
            
            try:
                # Extract Google Drive file ID
                file_id = extract_google_drive_id(audio_url)
                if not file_id:
                    results["failed"] += 1
                    results["errors"].append({
                        "row_id": row_id,
                        "error": "Could not extract Google Drive file ID",
                        "url": audio_url
                    })
                    continue
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file_path = tmp_file.name
                
                try:
                    # Download from Google Drive
                    print(f"Downloading file {file_id} for row {row_id}...")
                    if not download_from_google_drive(file_id, tmp_file_path):
                        results["failed"] += 1
                        results["errors"].append({
                            "row_id": row_id,
                            "error": "Failed to download from Google Drive",
                            "file_id": file_id
                        })
                        continue
                    
                    # Upload to GCS with organized path
                    destination_blob_name = f"listening_tarea1/{file_id}.mp3"
                    print(f"Uploading to GCS: {destination_blob_name}...")
                    bucket_url = upload_to_gcs(tmp_file_path, destination_blob_name)
                    
                    if not bucket_url:
                        results["failed"] += 1
                        results["errors"].append({
                            "row_id": row_id,
                            "error": "Failed to upload to GCS",
                            "file_id": file_id
                        })
                        continue
                    
                    # Update database
                    if not test_mode:
                        update_bucket_url(conn, row_id, bucket_url)
                        print(f"Updated row {row_id} with bucket URL: {bucket_url}")
                    else:
                        print(f"[TEST MODE] Would update row {row_id} with: {bucket_url}")
                    
                    results["successful"] += 1
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row_id": row_id,
                    "error": str(e),
                    "url": audio_url
                })
                print(f"Error processing row {row_id}: {str(e)}")
        
        cursor.close()
        
        return {
            "success": True,
            "message": "Migration completed",
            "results": results,
            "test_mode": test_mode
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": results
        }
    finally:
        if conn:
            conn.close()


@app.get("/start-migration")
async def start_auto_migration():
    """
    🚀 AUTO-MIGRATION ENDPOINT
    
    This endpoint automatically migrates all pending audio files in batches.
    Just visit this URL and it will handle everything!
    
    It will:
    1. Check current migration status
    2. Migrate all pending files in batches of 10
    3. Return final statistics
    
    Safe to run multiple times - skips already migrated files.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Ensure column exists
        try:
            cursor.execute("""
                ALTER TABLE listening_tarea1_set 
                ADD COLUMN IF NOT EXISTS bucket_url TEXT;
            """)
            conn.commit()
        except Exception as e:
            conn.rollback()
        
        # Get initial stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(audio_url) as rows_with_audio_url,
                COUNT(bucket_url) as rows_with_bucket_url,
                COUNT(CASE WHEN audio_url IS NOT NULL AND (bucket_url IS NULL OR bucket_url = '') THEN 1 END) as pending_migration
            FROM listening_tarea1_set;
        """)
        initial_stats = dict(cursor.fetchone())
        
        cursor.close()
        conn.close()
        
        # If nothing to migrate
        if initial_stats['pending_migration'] == 0:
            return {
                "success": True,
                "message": "✅ All files already migrated!",
                "statistics": initial_stats,
                "migrated_in_this_run": 0
            }
        
        # Migrate all pending files (batch size: 10)
        BATCH_SIZE = 10
        total_migrated = 0
        all_results = []
        
        while True:
            # Migrate one batch
            result = await migrate_audio_files(limit=BATCH_SIZE, test_mode=False)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": "Migration failed",
                    "details": result,
                    "total_migrated_before_error": total_migrated
                }
            
            batch_success = result["results"]["successful"]
            total_migrated += batch_success
            all_results.append(result["results"])
            
            # If this batch had no successful migrations, we're done
            if batch_success == 0:
                break
        
        # Get final stats
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(audio_url) as rows_with_audio_url,
                COUNT(bucket_url) as rows_with_bucket_url,
                COUNT(CASE WHEN audio_url IS NOT NULL AND (bucket_url IS NULL OR bucket_url = '') THEN 1 END) as pending_migration
            FROM listening_tarea1_set;
        """)
        final_stats = dict(cursor.fetchone())
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"✅ Migration completed! Migrated {total_migrated} files.",
            "migrated_in_this_run": total_migrated,
            "initial_statistics": initial_stats,
            "final_statistics": final_stats,
            "batch_results": all_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/migration-status")
async def get_migration_status():
    """
    Check the migration status of audio files
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='listening_tarea1_set' 
            AND column_name='bucket_url';
        """)
        column_exists = cursor.fetchone() is not None
        
        if not column_exists:
            return {
                "column_exists": False,
                "message": "bucket_url column does not exist yet"
            }
        
        # Get statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(audio_url) as rows_with_audio_url,
                COUNT(bucket_url) as rows_with_bucket_url,
                COUNT(CASE WHEN audio_url IS NOT NULL AND (bucket_url IS NULL OR bucket_url = '') THEN 1 END) as pending_migration
            FROM listening_tarea1_set;
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "column_exists": True,
            "statistics": dict(stats)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

