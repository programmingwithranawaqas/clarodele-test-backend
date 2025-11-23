#!/usr/bin/env python3
"""
Run Writing Parser from Cloud Run
This script will:
1. Drop existing writing_tarea1 tables
2. Recreate them from schema
3. Parse and insert all 100 documents
"""

import os
import sys
from parse_writing_tarea1 import get_db_connection, recreate_tables, parse_all_documents


def main():
    print("=" * 80)
    print("WRITING TAREA 1 - FULL DEPLOYMENT")
    print("=" * 80)
    
    folder_path = "Writing_Tarea_1"
    module_type_id = 1
    
    if not os.path.exists(folder_path):
        print(f"❌ Error: Folder '{folder_path}' not found!")
        sys.exit(1)
    
    try:
        # Step 1: Recreate tables
        print("\n🔄 Step 1: Recreating database tables...")
        conn = get_db_connection()
        recreate_tables(conn)
        conn.close()
        print("✅ Tables recreated successfully!")
        
        # Step 2: Parse and insert all documents
        print("\n🔄 Step 2: Parsing and inserting all documents...")
        results = parse_all_documents(
            folder_path=folder_path,
            module_type_id=module_type_id,
            limit=None,  # Process all files
            dry_run=False  # Insert into database
        )
        
        # Step 3: Summary
        print("\n" + "=" * 80)
        print("DEPLOYMENT COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully processed: {results['successful']}/{results['total']}")
        print(f"❌ Failed: {results['failed']}")
        
        if results['successful'] == results['total']:
            print("\n🎉 All documents parsed and inserted successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ Some documents failed to process")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
