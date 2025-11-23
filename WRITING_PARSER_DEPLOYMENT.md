# Writing Parser Deployment Guide

## ✅ What's Ready

The writing parser is now **100% functional** and tested on all 100 documents with:
- Audio URL properly extracted (no contamination)
- All metadata fields captured (word_limit, text_type, register)
- Complete text preservation (no data loss)
- Automatic table recreation from schema

## 🚀 Deployment Options

### Option 1: One-Click from Cloud Run UI (RECOMMENDED)

After deploying your code to Cloud Run:

1. **Open your Cloud Run service URL** in browser
2. **Click the button**: `🔄 Recreate Tables & Parse All Documents`
3. **Confirm the warning** (this will drop existing tables)
4. **Wait 2-3 minutes** for all 100 documents to process
5. **Check the results** - should show 100/100 successful

### Option 2: API Endpoint from Command Line

```bash
# Call the endpoint directly
curl -X POST https://your-cloudrun-url.run.app/recreate-and-parse-writing-tarea1
```

### Option 3: Run Standalone Script

```bash
# SSH into Cloud Run instance (if you have shell access)
python3 run_writing_parser.py
```

## 📊 Verify Success

After deployment, check the status:

```bash
curl https://your-cloudrun-url.run.app/writing-tarea1-status
```

Expected response:
```json
{
  "success": true,
  "folder": {
    "total_files": 100,
    "folder_exists": true
  },
  "database": {
    "total_records": 100,
    "with_situation": 100,
    "with_task": 100,
    "with_solution": 100
  },
  "pending": 0
}
```

## 🔧 What the Endpoint Does

The `POST /recreate-and-parse-writing-tarea1` endpoint:

1. **Drops** existing tables: `writing_tarea1_solution`, `writing_tarea1_set`
2. **Recreates** tables from `writing_tarea1_schema.sql`
3. **Parses** all 100 .docx files from `Writing_Tarea_1/` folder
4. **Inserts** extracted data into database tables
5. **Returns** success/failure summary

## 📋 Database Tables Created

### `writing_tarea1_set`
- `tarea1_set_id` (serial primary key)
- `title` (varchar 255)
- `situation` (text)
- `task_instructions` (text)
- `word_limit` (varchar 100)
- `text_type` (varchar 100)
- `register` (varchar 100)
- `reminders` (text)
- `audio_url` (varchar 500)
- `module_type_id` (integer)
- `created_at` (timestamp)

### `writing_tarea1_solution`
- `solution_id` (serial primary key)
- `tarea1_set_id` (foreign key → writing_tarea1_set)
- `solution_text` (text)

## ⚠️ Important Notes

- **Data Loss Warning**: The recreate endpoint DROPS existing tables
- **Processing Time**: Expect 2-3 minutes for 100 documents
- **Memory**: Ensure Cloud Run instance has sufficient memory (512MB+ recommended)
- **Dependencies**: Requires `python-docx` in requirements.txt (already added)

## 🧪 Testing Locally (Optional)

If you want to test locally before Cloud Run deployment:

```bash
# Test parser only (no database)
python3 parse_writing_tarea1.py --dry-run

# Test first 5 documents with database
python3 parse_writing_tarea1.py --limit 5

# Full deployment with table recreation
python3 parse_writing_tarea1.py --recreate-tables
```

## 📝 Next Steps

1. Deploy updated code to Cloud Run
2. Open Cloud Run URL in browser
3. Click "Recreate Tables & Parse All Documents" button
4. Verify 100/100 success
5. Check database tables in Supabase

All code has been committed and pushed to GitHub (commit aa798fa).
