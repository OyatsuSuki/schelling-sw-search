from pathlib import Path
import sqlite3
import sys
import re
import json

DEFAULT_DATABASE = "corpus/database/schelling.db"
CORRECTIONS_FILE = "corpus/data/schelling_ocr_corrections.json"

def parse_args(args):
    options = {
        "work": None,
        "volume": None,
        "from_page": None,
        "to_page": None,
        "context": 220,
        "limit": 20,
        "footnotes": False,
        "raw": False
    }
    
    clean_args = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--work" and i + 1 < len(args):
            options["work"] = args[i+1]
            i += 2
        elif arg == "--volume" and i + 1 < len(args):
            options["volume"] = args[i+1]
            i += 2
        elif arg == "--from" and i + 1 < len(args):
            options["from_page"] = args[i+1]
            i += 2
        elif arg == "--to" and i + 1 < len(args):
            options["to_page"] = args[i+1]
            i += 2
        elif arg == "--context" and i + 1 < len(args):
            options["context"] = int(args[i+1])
            i += 2
        elif arg == "--limit" and i + 1 < len(args):
            val = args[i+1].lower()
            options["limit"] = 0 if val == "all" else int(val)
            i += 2
        elif arg == "--footnotes":
            options["footnotes"] = True
            i += 1
        elif arg == "--raw":
            options["raw"] = True
            i += 1
        else:
            clean_args.append(arg)
            i += 1
            
    return clean_args, options

def load_corrections(filepath):
    path = Path(filepath)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k: v.get("correction", k) for k, v in data.items()}
    except Exception as e:
        return {}

def apply_corrections(text, corrections):
    if not corrections or not text:
        return text
    for corrupted in sorted(corrections.keys(), key=len, reverse=True):
        corrected = corrections[corrupted]
        text = text.replace(corrupted, corrected)
    return text

def parse_query(parts):
    if not parts:
        return None

    raw_query = " ".join(parts).strip()
    if not raw_query:
        return None

    raw_query = re.sub(r'[“”„«»]', '"', raw_query)

    phrases = []
    def extract_phrase(match):
        phrase = match.group(1).strip()
        if phrase:
            phrases.append(phrase)
        return " "

    remaining = re.sub(r'"([^"]+)"', extract_phrase, raw_query)
    terms = [t.strip() for t in re.findall(r"\S+", remaining) if t.strip()]

    fts_parts = []
    for phrase in phrases:
        escaped = phrase.replace('"', '""')
        fts_parts.append(f'"{escaped}"')
    for term in terms:
        escaped = term.replace('"', '""')
        fts_parts.append(f'"{escaped}"')

    if not fts_parts:
        return None

    fts_query = " AND ".join(fts_parts)
    
    return {
        "display": raw_query,
        "fts": fts_query,
        "terms": terms,
        "phrases": phrases,
    }

def query_search_targets(query_info):
    targets = []
    for phrase in query_info["phrases"]:
        if phrase: targets.append(phrase)
    for term in query_info["terms"]:
        if term: targets.append(term)
    return targets

def clean_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()

def make_snippet(text, query_info, context_width):
    text = clean_whitespace(text)
    if not text:
        return ""
    targets = query_search_targets(query_info)
    if not targets:
        return text[:context_width]
    
    matches = []
    for target in targets:
        if not target: continue
        for m in re.finditer(re.escape(target), text, flags=re.IGNORECASE):
            matches.append((m.start(), m.end()))
    
    if not matches:
        return text[:context_width]
        
    matches.sort(key=lambda x: x[0])
    
    half_width = context_width // 2
    
    windows = []
    for start, end in matches:
        windows.append([max(0, start - half_width), min(len(text), end + half_width)])
        
    merged = []
    for w in windows:
        if not merged:
            merged.append(w)
        else:
            last = merged[-1]
            if w[0] <= last[1] + 20: 
                last[1] = max(last[1], w[1])
            else:
                merged.append(w)

    snippets = []
    for w_start, w_end in merged:
        segment = text[w_start:w_end]
        if w_start > 0:
            segment = "... " + segment.lstrip()
        if w_end < len(text):
            segment = segment.rstrip() + " ..."
        snippets.append(segment)
        
    return "  \n\n**[ ... ]**  \n\n".join(snippets)

def search_database(database_path, query_info, options):
    database_path = Path(database_path)
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found:\n{database_path.resolve()}")
        
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    conditions = ["pages_fts MATCH ?"]
    params = [query_info["fts"]]
    
    if options["work"]:
        conditions.append("pages.work_title = ?")
        params.append(options["work"])
        
    if options["volume"]:
        parts = options["volume"].split(",")
        if len(parts) == 2:
            conditions.append("pages.division = ? AND pages.volume = ?")
            params.extend([parts[0], int(parts[1])])

    from_rowid, to_rowid = None, None
    if options["from_page"] and options["to_page"]:
        cursor.execute("SELECT rowid FROM pages WHERE sw_page_label = ?", (options["from_page"],))
        row_from = cursor.fetchone()
        if row_from: from_rowid = row_from[0]
        
        cursor.execute("SELECT rowid FROM pages WHERE sw_page_label = ?", (options["to_page"],))
        row_to = cursor.fetchone()
        if row_to: to_rowid = row_to[0]
        
        if from_rowid and to_rowid:
            start_id = min(from_rowid, to_rowid)
            end_id = max(from_rowid, to_rowid)
            conditions.append("pages.rowid BETWEEN ? AND ?")
            params.extend([start_id, end_id])

    where_clause = " AND ".join(conditions)
    
    sql = f"""
    SELECT
        pages.id,
        pages.division,
        pages.volume,
        pages.sw_page,
        pages.sw_page_label,
        pages.pdf_pages,
        pages.body,
        pages.work_title,
        bm25(pages_fts) AS rank,
        NULL AS footnote_number
    FROM pages_fts
    JOIN pages ON pages.rowid = pages_fts.rowid
    WHERE {where_clause}
    """
    cursor.execute(sql, params)
    results = [dict(r) for r in cursor.fetchall()]

    if options["footnotes"]:
        fn_conditions = []
        fn_params = []
        targets = query_search_targets(query_info)
        
        for target in targets:
            fn_conditions.append("footnotes.text LIKE ?")
            fn_params.append(f"%{target}%")
            
        if fn_conditions:
            fn_where = " AND ".join(fn_conditions)
            
            if options["work"]:
                fn_where += " AND pages.work_title = ?"
                fn_params.append(options["work"])
                
            if options["volume"]:
                parts = options["volume"].split(",")
                if len(parts) == 2:
                    fn_where += " AND pages.division = ? AND pages.volume = ?"
                    fn_params.extend([parts[0], int(parts[1])])
                    
            if from_rowid and to_rowid:
                fn_where += " AND pages.rowid BETWEEN ? AND ?"
                fn_params.extend([min(from_rowid, to_rowid), max(from_rowid, to_rowid)])
                
            fn_sql = f"""
            SELECT
                pages.id,
                pages.division,
                pages.volume,
                pages.sw_page,
                pages.sw_page_label,
                pages.pdf_pages,
                footnotes.text AS body,
                pages.work_title,
                0 AS rank,
                footnotes.footnote_number
            FROM footnotes
            JOIN pages ON pages.id = footnotes.page_id
            WHERE {fn_where}
            """
            cursor.execute(fn_sql, fn_params)
            fn_results = [dict(r) for r in cursor.fetchall()]
            results.extend(fn_results)
            
    connection.close()

    def sw_sort_key(x):
        div_weight = 1 if x["division"] == "I" else 2
        vol = int(x["volume"])
        page = int(x["sw_page"])
        fn_weight = 0
        if x["footnote_number"]:
            match = re.search(r'\d+', str(x["footnote_number"]))
            fn_weight = int(match.group()) if match else 999
        return (div_weight, vol, page, fn_weight)

    results.sort(key=sw_sort_key)
    
    if options["limit"] > 0:
        results = results[:options["limit"]]

    return results

def main():
    pass

if __name__ == "__main__":
    main()