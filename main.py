from fastapi import FastAPI
from google.cloud import storage

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Cloud Run test backend!"}

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
