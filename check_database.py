#!/usr/bin/env python3
"""
Database Connection and Table Structure Checker

This script verifies:
1. Database connection is working
2. Table exists and structure
3. Current data statistics
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require"
)

TABLE_NAME = "listening_tarea1_set"


def main():
    print("="*70)
    print("Database Connection & Table Structure Checker")
    print("="*70)
    print()
    
    try:
        # Test connection
        print("1. Testing database connection...")
        conn = psycopg2.connect(DATABASE_URL)
        print("   ✓ Successfully connected to database")
        print()
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if table exists
        print(f"2. Checking if table '{TABLE_NAME}' exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (TABLE_NAME,))
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            print(f"   ✗ Table '{TABLE_NAME}' does not exist!")
            return
        
        print(f"   ✓ Table '{TABLE_NAME}' exists")
        print()
        
        # Get table structure
        print("3. Checking table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (TABLE_NAME,))
        
        columns = cursor.fetchall()
        print(f"   Found {len(columns)} columns:")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"     - {col['column_name']}: {col['data_type']} ({nullable})")
        print()
        
        # Check for required columns
        print("4. Checking for required columns...")
        column_names = [col['column_name'] for col in columns]
        
        required_columns = ['tarea1_set_id', 'audio_url']
        for req_col in required_columns:
            if req_col in column_names:
                print(f"   ✓ '{req_col}' column exists")
            else:
                print(f"   ✗ '{req_col}' column missing!")
        
        if 'bucket_url' in column_names:
            print(f"   ✓ 'bucket_url' column exists (migration ready)")
        else:
            print(f"   ⚠️  'bucket_url' column does not exist (will be created by migration script)")
        print()
        
        # Get data statistics
        print("5. Getting data statistics...")
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(audio_url) as rows_with_audio_url,
                COUNT(CASE WHEN audio_url IS NULL OR audio_url = '' THEN 1 END) as rows_without_audio_url
            FROM {TABLE_NAME};
        """)
        
        stats = cursor.fetchone()
        print(f"   Total rows: {stats['total_rows']}")
        print(f"   Rows with audio_url: {stats['rows_with_audio_url']}")
        print(f"   Rows without audio_url: {stats['rows_without_audio_url']}")
        print()
        
        # Check bucket_url statistics if column exists
        if 'bucket_url' in column_names:
            print("6. Checking migration status...")
            cursor.execute(f"""
                SELECT 
                    COUNT(bucket_url) as migrated,
                    COUNT(CASE WHEN audio_url IS NOT NULL AND (bucket_url IS NULL OR bucket_url = '') THEN 1 END) as pending
                FROM {TABLE_NAME};
            """)
            
            migration_stats = cursor.fetchone()
            print(f"   Already migrated: {migration_stats['migrated']}")
            print(f"   Pending migration: {migration_stats['pending']}")
            
            if migration_stats['pending'] > 0:
                print(f"   → Ready to migrate {migration_stats['pending']} files")
            elif migration_stats['migrated'] > 0:
                print(f"   ✓ All files have been migrated!")
            else:
                print(f"   ⚠️  No files to migrate")
            print()
        
        # Show sample data
        print("7. Sample data (first 3 rows with audio_url)...")
        cursor.execute(f"""
            SELECT tarea1_set_id as id, 
                   SUBSTRING(audio_url, 1, 60) as audio_url_preview,
                   {'SUBSTRING(bucket_url, 1, 60) as bucket_url_preview' if 'bucket_url' in column_names else "'' as bucket_url_preview"}
            FROM {TABLE_NAME}
            WHERE audio_url IS NOT NULL
            LIMIT 3;
        """)
        
        samples = cursor.fetchall()
        for i, row in enumerate(samples, 1):
            print(f"\n   Row {i} (ID: {row['id']}):")
            print(f"     audio_url: {row['audio_url_preview']}...")
            if 'bucket_url' in column_names and row.get('bucket_url_preview'):
                print(f"     bucket_url: {row['bucket_url_preview']}...")
            else:
                print(f"     bucket_url: (not set)")
        
        print()
        print("="*70)
        print("✓ All checks completed successfully!")
        print("="*70)
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        print("\nPossible issues:")
        print("  - Check if DATABASE_URL is correct")
        print("  - Verify your IP is whitelisted in Supabase")
        print("  - Ensure SSL mode is supported")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
