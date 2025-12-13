#!/usr/bin/env python3
"""
Oral Tarea 2 parser
- Reads all .docx files inside Oral_Tarea_2/
- Extracts image URL, audio URL, and solution text
- Inserts into oral_tarea2_set and oral_tarea2_solution tables
- Uses the provided universal instructions text for every row
"""

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from docx import Document

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:%40%21ceXpert%2C9%2F11@db.ycnqrnacilcwqqgelaod.supabase.co:5432/postgres?sslmode=require",
)

# Default module_type_id for "Expresión e Interacción Orales" (adjust via env or CLI)
DEFAULT_MODULE_TYPE_ID = int(os.getenv("ORAL_TAREA2_MODULE_TYPE_ID", "6"))

# Fixed instructions text provided by the user
DEFAULT_INSTRUCTIONS = (
    "Observa la imagen y describe lo que ves durante 1-2 minutos:\n"
    "En tu descripción debes:\n"
    "Describir las personas, objetos y el lugar que aparecen\n"
    "Explicar qué están haciendo las personas\n"
    "Dar tu opinión sobre la situación representada\n"
    "Relacionar la imagen con experiencias personales si es posible"
)


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(DATABASE_URL)


def _strip_lines(doc: Document) -> List[str]:
    """Return a list of non-empty trimmed lines from a docx document."""
    lines: List[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines


def _find_labeled_value(lines: List[str], label: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Find the first occurrence of a label (case-insensitive) and return the next non-empty line as its value.
    Returns (value, value_index).
    """
    target = label.lower()
    for idx, line in enumerate(lines):
        if line.lower() == target:
            # Pick the next non-empty line
            for j in range(idx + 1, len(lines)):
                if lines[j].strip():
                    return lines[j].strip(), j
    return None, None


def parse_oral_tarea2_document(path: Path) -> Dict[str, Optional[str]]:
    """
    Parse a single Oral Tarea 2 .docx file.
    Expected minimal structure:
      Image_url\n<image-url>\nAudio_url\n<audio-url>\nSolution\n<solution text ...>
    """
    doc = Document(path)
    lines = _strip_lines(doc)

    image_url, _ = _find_labeled_value(lines, "image_url")
    audio_url, audio_idx = _find_labeled_value(lines, "audio_url")

    # Solution starts after the first "Solution" line; join the remaining lines
    solution_text = None
    for idx, line in enumerate(lines):
        if line.lower() == "solution":
            remaining = [ln.strip() for ln in lines[idx + 1 :] if ln.strip()]
            solution_text = "\n".join(remaining) if remaining else None
            break

    if not image_url:
        raise ValueError(f"Missing image_url in {path.name}")
    if not audio_url:
        raise ValueError(f"Missing audio_url in {path.name}")
    if not solution_text:
        raise ValueError(f"Missing solution text in {path.name}")

    return {
        "image_url": image_url,
        "audio_url": audio_url,
        "solution_text": solution_text,
    }


def insert_oral_tarea2(conn, data: Dict[str, str], module_type_id: int, instructions: str) -> int:
    """Insert into oral_tarea2_set and oral_tarea2_solution; return tarea2_set_id."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO oral_tarea2_set (module_type_id, instructions, image_url)
        VALUES (%s, %s, %s)
        RETURNING tarea2_set_id;
        """,
        (module_type_id, instructions, data["image_url"]),
    )
    tarea2_set_id = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO oral_tarea2_solution (tarea2_set_id, solution_text, audio_url, bucket_url)
        VALUES (%s, %s, %s, %s);
        """,
        (tarea2_set_id, data["solution_text"], data["audio_url"], None),
    )

    conn.commit()
    cursor.close()
    return tarea2_set_id


def parse_all_documents(
    folder_path: str = "Oral_Tarea_2",
    module_type_id: int = DEFAULT_MODULE_TYPE_ID,
    instructions: str = DEFAULT_INSTRUCTIONS,
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Parse all .docx files in folder_path and insert into the database.
    Returns summary counts.
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = sorted(folder.glob("*.docx"), key=lambda p: p.name)
    if limit:
        files = files[:limit]

    total = len(files)
    success = 0
    failed = 0
    errors: List[Dict[str, str]] = []

    conn = None
    try:
        conn = get_db_connection()
        for path in files:
            try:
                data = parse_oral_tarea2_document(path)
                if dry_run:
                    success += 1
                    continue
                insert_oral_tarea2(conn, data, module_type_id, instructions)
                success += 1
            except Exception as exc:  # pragma: no cover - defensive
                failed += 1
                errors.append({"file": path.name, "error": str(exc)})
                if conn:
                    conn.rollback()
    finally:
        if conn:
            conn.close()

    return {"total": total, "successful": success, "failed": failed, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Parse Oral Tarea 2 .docx files and load into Postgres")
    parser.add_argument("--folder", default="Oral_Tarea_2", help="Folder containing .docx files")
    parser.add_argument("--module-type-id", type=int, default=DEFAULT_MODULE_TYPE_ID, help="module_type_id to use")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Parse files without inserting into DB")
    args = parser.parse_args()

    summary = parse_all_documents(
        folder_path=args.folder,
        module_type_id=args.module_type_id,
        instructions=DEFAULT_INSTRUCTIONS,
        limit=args.limit,
        dry_run=args.dry_run,
    )

    print("\n=== Oral Tarea 2 Parsing Summary ===")
    print(f"Total files:      {summary['total']}")
    print(f"Successful:       {summary['successful']}")
    print(f"Failed:           {summary['failed']}")
    if summary.get("errors"):
        print("Errors:")
        for err in summary["errors"][:10]:
            print(f"  - {err['file']}: {err['error']}")


if __name__ == "__main__":
    main()
