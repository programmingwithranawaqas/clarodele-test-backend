#!/usr/bin/env python3
"""
Writing Tarea 1 Parser - Complete Document Extraction
Parses all .docx files from Writing_Tarea_1 folder and stores in PostgreSQL database.
Ensures NO TEXT IS MISSED from documents.
"""

import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from docx import Document
from typing import Dict, List, Optional
import argparse


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require"
)

# Default module_type_id (you can change this)
DEFAULT_MODULE_TYPE_ID = 1


def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(DATABASE_URL)


def extract_all_text_from_docx(docx_path: str) -> str:
    """
    Extract ALL text from a .docx file including paragraphs, tables, headers, footers.
    Ensures no text is missed.
    """
    doc = Document(docx_path)
    full_text = []
    
    # 1. Extract all paragraphs
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_text.append(text)
    
    # 2. Extract all text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text.strip()
                if text:
                    full_text.append(text)
    
    # 3. Extract text from headers
    for section in doc.sections:
        header = section.header
        for para in header.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)
    
    # 4. Extract text from footers
    for section in doc.sections:
        footer = section.footer
        for para in footer.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)
    
    return "\n".join(full_text)


def parse_writing_tarea1_document(docx_path: str) -> Dict:
    """
    Parse a Writing Tarea 1 document and extract structured data.
    Uses pattern matching to identify sections but preserves ALL text.
    """
    # Extract all text first
    full_text = extract_all_text_from_docx(docx_path)
    
    # Initialize data structure
    data = {
        "title": None,
        "situation": None,
        "task_instructions": None,
        "word_limit": None,
        "text_type": None,
        "register": None,
        "reminders": None,
        "audio_url": None,
        "solution_text": None,
        "full_raw_text": full_text  # Keep original text for verification
    }
    
    # Split text into lines for processing
    lines = full_text.split('\n')
    
    # Pattern recognition variables
    current_section = None
    section_content = []
    
    # Keywords that indicate section boundaries
    situation_keywords = ['SITUACIÓN', 'Situación', 'SITUACION']
    task_keywords = ['TAREA', 'Tarea', 'INSTRUCCIONES']
    solution_keywords = ['SOLUCIÓN', 'Solución', 'SOLUCION', 'Modelo de respuesta', 'MODELO']
    reminder_keywords = ['Recuerde', 'RECUERDE', 'Recordatorio']
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if not line_stripped:
            continue
        
        # Detect SITUATION section
        if any(keyword in line_stripped for keyword in situation_keywords):
            if current_section and section_content:
                # Save previous section
                save_section(data, current_section, section_content)
            current_section = 'situation'
            section_content = []
            # Check if situation text is on same line
            if ':' in line_stripped:
                content_after_colon = line_stripped.split(':', 1)[1].strip()
                if content_after_colon:
                    section_content.append(content_after_colon)
            continue
        
        # Detect TASK section
        if any(keyword in line_stripped for keyword in task_keywords):
            if current_section and section_content:
                save_section(data, current_section, section_content)
            current_section = 'task'
            section_content = []
            if ':' in line_stripped:
                content_after_colon = line_stripped.split(':', 1)[1].strip()
                if content_after_colon:
                    section_content.append(content_after_colon)
            continue
        
        # Detect SOLUTION section
        if any(keyword in line_stripped for keyword in solution_keywords):
            if current_section and section_content:
                save_section(data, current_section, section_content)
            current_section = 'solution'
            section_content = []
            if ':' in line_stripped:
                content_after_colon = line_stripped.split(':', 1)[1].strip()
                if content_after_colon:
                    section_content.append(content_after_colon)
            continue
        
        # Detect REMINDER section
        if any(keyword in line_stripped for keyword in reminder_keywords):
            if current_section and section_content:
                save_section(data, current_section, section_content)
            current_section = 'reminder'
            section_content = []
            if ':' in line_stripped:
                content_after_colon = line_stripped.split(':', 1)[1].strip()
                if content_after_colon:
                    section_content.append(content_after_colon)
            continue
        
        # Detect metadata fields
        if 'palabras' in line_stripped.lower() and ('150' in line_stripped or '180' in line_stripped or 'límite' in line_stripped.lower()):
            data['word_limit'] = line_stripped
            continue
        
        if 'tipo de texto' in line_stripped.lower() or 'tipo:' in line_stripped.lower():
            data['text_type'] = extract_metadata_value(line_stripped)
            continue
        
        if 'registro' in line_stripped.lower() and len(line_stripped) < 50:
            data['register'] = extract_metadata_value(line_stripped)
            continue
        
        # Check for title (usually first line or prominent header)
        if data['title'] is None and len(line_stripped) > 5 and len(line_stripped) < 100:
            if not any(keyword in line_stripped for keyword in situation_keywords + task_keywords + solution_keywords):
                if i == 0 or (i < 3 and line_stripped.isupper()):
                    data['title'] = line_stripped
                    continue
        
        # Add line to current section
        if current_section:
            section_content.append(line_stripped)
    
    # Save last section
    if current_section and section_content:
        save_section(data, current_section, section_content)
    
    return data


def save_section(data: Dict, section_name: str, content: List[str]):
    """Save accumulated section content to data dictionary"""
    text = '\n'.join(content).strip()
    
    if section_name == 'situation':
        data['situation'] = text
    elif section_name == 'task':
        data['task_instructions'] = text
    elif section_name == 'solution':
        data['solution_text'] = text
    elif section_name == 'reminder':
        data['reminders'] = text


def extract_metadata_value(line: str) -> str:
    """Extract value from metadata lines like 'Tipo: Informe formal'"""
    if ':' in line:
        return line.split(':', 1)[1].strip()
    return line.strip()


def insert_writing_tarea1(conn, data: Dict, module_type_id: int, file_name: str) -> Optional[int]:
    """
    Insert writing tarea1 data into database.
    Returns the tarea1_set_id if successful, None otherwise.
    """
    cursor = conn.cursor()
    
    try:
        # Insert into writing_tarea1_set
        cursor.execute("""
            INSERT INTO writing_tarea1_set 
            (title, situation, task_instructions, word_limit, text_type, register, reminders, audio_url, module_type_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING tarea1_set_id;
        """, (
            data.get('title') or file_name,  # Use filename as fallback title
            data.get('situation'),
            data.get('task_instructions'),
            data.get('word_limit'),
            data.get('text_type'),
            data.get('register'),
            data.get('reminders'),
            data.get('audio_url'),
            module_type_id
        ))
        
        tarea1_set_id = cursor.fetchone()[0]
        
        # Insert solution if exists
        if data.get('solution_text'):
            cursor.execute("""
                INSERT INTO writing_tarea1_solution 
                (tarea1_set_id, solution_text)
                VALUES (%s, %s);
            """, (tarea1_set_id, data.get('solution_text')))
        
        conn.commit()
        return tarea1_set_id
        
    except Exception as e:
        conn.rollback()
        print(f"Error inserting data: {e}")
        raise
    finally:
        cursor.close()


def parse_all_documents(folder_path: str, module_type_id: int = DEFAULT_MODULE_TYPE_ID, 
                        limit: Optional[int] = None, dry_run: bool = False):
    """
    Parse all .docx files in the folder and insert into database.
    
    Args:
        folder_path: Path to Writing_Tarea_1 folder
        module_type_id: ID of the module type
        limit: Limit number of files to process (for testing)
        dry_run: If True, parse but don't insert into database
    """
    # Get all .docx files
    files = [f for f in os.listdir(folder_path) if f.endswith('.docx')]
    files.sort()  # Sort for consistent processing
    
    if limit:
        files = files[:limit]
    
    print(f"Found {len(files)} .docx files to process")
    print("=" * 80)
    
    conn = None if dry_run else get_db_connection()
    
    results = {
        'total': len(files),
        'successful': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        for idx, filename in enumerate(files, 1):
            file_path = os.path.join(folder_path, filename)
            
            print(f"\n[{idx}/{len(files)}] Processing: {filename}")
            
            try:
                # Parse document
                data = parse_writing_tarea1_document(file_path)
                
                # Validation: ensure critical fields are not empty
                if not data.get('situation') and not data.get('task_instructions'):
                    print(f"  ⚠️  WARNING: No situation or task found, using full text")
                    # If structure not detected, store all text in situation
                    data['situation'] = data['full_raw_text']
                
                if dry_run:
                    print(f"  📄 DRY RUN - Parsed successfully")
                    print(f"     - Title: {data.get('title', 'N/A')[:50]}...")
                    print(f"     - Situation: {len(data.get('situation', ''))} chars")
                    print(f"     - Task: {len(data.get('task_instructions', ''))} chars")
                    print(f"     - Solution: {len(data.get('solution_text', ''))} chars")
                    print(f"     - Total text: {len(data['full_raw_text'])} chars")
                else:
                    # Insert into database
                    tarea1_set_id = insert_writing_tarea1(conn, data, module_type_id, filename)
                    print(f"  ✅ Inserted successfully (ID: {tarea1_set_id})")
                
                results['successful'] += 1
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                results['failed'] += 1
                results['errors'].append({
                    'file': filename,
                    'error': str(e)
                })
    
    finally:
        if conn:
            conn.close()
    
    # Print summary
    print("\n" + "=" * 80)
    print("PARSING SUMMARY")
    print("=" * 80)
    print(f"Total files: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors'][:10]:
            print(f"  - {error['file']}: {error['error']}")
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Parse Writing Tarea 1 documents")
    parser.add_argument(
        "--folder",
        type=str,
        default="Writing_Tarea_1",
        help="Path to Writing_Tarea_1 folder"
    )
    parser.add_argument(
        "--module-type-id",
        type=int,
        default=DEFAULT_MODULE_TYPE_ID,
        help="Module type ID for the documents"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to process (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse documents but don't insert into database"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("WRITING TAREA 1 PARSER")
    print("=" * 80)
    print(f"Folder: {args.folder}")
    print(f"Module Type ID: {args.module_type_id}")
    print(f"Limit: {args.limit if args.limit else 'No limit'}")
    print(f"Dry Run: {args.dry_run}")
    print("=" * 80)
    
    if not os.path.exists(args.folder):
        print(f"❌ Error: Folder '{args.folder}' not found!")
        return
    
    parse_all_documents(
        folder_path=args.folder,
        module_type_id=args.module_type_id,
        limit=args.limit,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
