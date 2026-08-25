from pathlib import Path
import json
import sqlite3
import sys

DEFAULT_DATABASE = "corpus/database/schelling.db"
CORRECTIONS_FILE = "corpus/data/schelling_ocr_corrections.json"

def load_corrections(filepath):
    path = Path(filepath)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: v.get("correction", k) for k, v in data.items()}
    except Exception as e:
        print(f"Error loading corrections: {e}")
        return {}

def apply_corrections(text, corrections):
    if not corrections or not text:
        return text
    for corrupted in sorted(corrections.keys(), key=len, reverse=True):
        corrected = corrections[corrupted]
        text = text.replace(corrupted, corrected)
    return text

def get_page(database_path, sw_page_label):
    database_path = Path(database_path)
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found:\n{database_path.resolve()}")
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, author, source, division, volume, sw_page, sw_page_label, pdf_pages, body, work_title
        FROM pages WHERE sw_page_label = ?
        """, (sw_page_label,)
    )
    page = cursor.fetchone()
    if page is None:
        connection.close()
        return None, []
    cursor.execute(
        """
        SELECT footnote_number, text FROM footnotes WHERE page_id = ?
        ORDER BY CAST(footnote_number AS INTEGER), footnote_number
        """, (page["id"],)
    )
    footnotes = cursor.fetchall()
    connection.close()
    return dict(page), [dict(fn) for fn in footnotes]

def parse_pdf_pages(value):
    try:
        pages = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(pages, list):
        return []
    return pages

def main():
    pass

if __name__ == "__main__":
    main()