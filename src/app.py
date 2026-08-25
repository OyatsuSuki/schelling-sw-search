import sys
from pathlib import Path
import sqlite3
import re
import json
from collections import Counter, defaultdict
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent))
import search_corpus as sc
import show_page as sp

st.set_page_config(page_title="Schelling Sämmtliche Werke", layout="wide", initial_sidebar_state="expanded")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display: none;}
            header {background-color: transparent !important;}
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "全文检索 (Volltextsuche)"
if 'reader_mode' not in st.session_state:
    st.session_state.reader_mode = 'single_page'
if 'reader_page' not in st.session_state:
    st.session_state.reader_page = 'I,1,1'
if 'reader_nav' not in st.session_state:
    st.session_state.reader_nav = {'div': 'I', 'vol': 1, 'work': ''}

@st.cache_data
def load_global_corrections():
    return sc.load_corrections(sc.CORRECTIONS_FILE)

@st.cache_data
def load_works():
    conn = sqlite3.connect(sc.DEFAULT_DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT work_title FROM pages WHERE work_title IS NOT NULL ORDER BY division, volume")
    works = [r[0] for r in cursor.fetchall()]
    conn.close()
    return works

@st.cache_data
def load_toc():
    conn = sqlite3.connect(sc.DEFAULT_DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT division, volume, work_title, MIN(rowid)
        FROM pages
        WHERE work_title IS NOT NULL
        GROUP BY division, volume, work_title
        ORDER BY MIN(rowid)
    """)
    rows = cursor.fetchall()
    conn.close()
    
    toc = {"I": {}, "II": {}}
    for r in rows:
        div, vol, work, _ = r
        if vol not in toc[div]:
            toc[div][vol] = []
        work_key = work if work else "Unklassifizierter Text"
        toc[div][vol].append(work_key)
    return toc

def get_continuous_pages(db_path, div, vol, work):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT id, sw_page_label, pdf_pages, body, work_title FROM pages WHERE division = ? AND volume = ? AND work_title = ? ORDER BY rowid"
    params = [div, vol, work]
        
    cursor.execute(query, params)
    pages = [dict(r) for r in cursor.fetchall()]
    
    footnotes = []
    if pages:
        page_ids = [str(p['id']) for p in pages]
        placeholders = ",".join("?" * len(page_ids))
        cursor.execute(f"SELECT page_id, footnote_number, text FROM footnotes WHERE page_id IN ({placeholders}) ORDER BY page_id, CAST(footnote_number AS INTEGER)", page_ids)
        footnotes = [dict(r) for r in cursor.fetchall()]
        
    conn.close()
    return pages, footnotes

def change_page(delta):
    conn = sqlite3.connect(sc.DEFAULT_DATABASE)
    c = conn.cursor()
    c.execute("SELECT rowid FROM pages WHERE sw_page_label = ?", (st.session_state.reader_page,))
    res = c.fetchone()
    if res:
        c.execute("SELECT sw_page_label FROM pages WHERE rowid = ?", (res[0] + delta,))
        new_res = c.fetchone()
        if new_res:
            st.session_state.reader_mode = 'single_page'
            st.session_state.reader_page = new_res[0]
    conn.close()

corrections = load_global_corrections()
available_works = load_works()

def render_page_block(p, page_fns, show_raw_flag):
    st.markdown(f"<div style='text-align: right; font-size: 0.85em; color: #888; margin-bottom: 10px;'>[SW {p['sw_page_label']}]</div>", unsafe_allow_html=True)
    
    body_text = p["body"] if show_raw_flag else sc.apply_corrections(p["body"], corrections)
    
    paragraphs = body_text.split("\n")
    html_body = ""
    for para in paragraphs:
        if para.strip():
            html_body += f"<p style='margin-bottom: 1em;'>{para.strip()}</p>"
            
    st.markdown(f"""
        <div lang="de" style="
            text-align: justify; 
            hyphens: auto; 
            word-wrap: break-word; 
            overflow-wrap: break-word; 
            line-height: 1.65; 
            font-size: 1.05em;
            margin-bottom: 20px;
        ">
            {html_body}
        </div>
    """, unsafe_allow_html=True)

    if page_fns:
        st.markdown("<hr style='margin: 5px 0px 15px 0px; border-top: 1px dashed #ddd;'/>", unsafe_allow_html=True)
        for fn in page_fns:
            fn_text = fn["text"] if show_raw_flag else sc.apply_corrections(fn["text"], corrections)
            st.markdown(f"""
                <div lang="de" style="
                    text-align: justify; 
                    hyphens: auto; 
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    font-size: 0.9em; 
                    color: #555; 
                    line-height: 1.45; 
                    margin-bottom: 8px;
                ">
                    <b>[{fn['footnote_number']}]</b> {fn_text}
                </div>
            """, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

STOP_WORDS = {
    "der", "die", "das", "und", "ist", "es", "in", "von", "zu", "nicht", 
    "sich", "mit", "ein", "eine", "einer", "eines", "einem", "für", "auf", 
    "auch", "als", "an", "was", "dem", "den", "des", "dass", "daß", "er", 
    "sie", "wir", "man", "aber", "oder", "um", "nur", "noch", "aus", "vor", 
    "wie", "doch", "so", "wird", "werden", "sein", "sind", "hat", "haben",
    "im", "am", "zur", "zum", "vom", "bei", "denn", "dann", "nach", "da",
    "ich", "mich", "mir", "du", "dich", "dir", "ihr", "ihnen", "uns", "dies",
    "diese", "dieser", "dieses", "diesem", "diesen", "jenes", "jener", "jene"
}

def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def get_words(sentence):
    words = re.findall(r"[a-zA-ZäöüÄÖÜß]+", sentence)
    return [w.lower() for w in words]

def sort_volume_key(vol_str):
    div, vol = vol_str.split(",")
    div_weight = 1 if div == "I" else 2
    return (div_weight, int(vol))

st.sidebar.title("Schelling Sämmtliche Werke")
app_mode = st.sidebar.radio("Funktionen", ["全文搜索", "原文", "词汇统计"], key="app_mode")
st.sidebar.markdown("---")
show_raw = st.sidebar.checkbox("显示原OCR文件的乱码", value=False)

if app_mode == "全文搜索":
    st.title("全文搜索")
    query_str = st.text_input("关键词", value="Freiheit")
    work_filter = st.selectbox("限定著作", [""] + available_works)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        vol_filter = st.text_input("指定分卷", value="")
    with col2:
        context_width = st.number_input("上下文范围", value=300, step=100)
    with col3:
        limit_val = st.number_input("返回数量 (Limit: 0 = alle)", value=50, step=10)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        include_footnotes = st.checkbox("包括脚注")
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)
        use_lemma = st.checkbox("匹配词形还原")

    if st.button("搜索", type="primary"):
        args = []
        if use_lemma and '"' not in query_str and ' ' not in query_str:
            args.append(f"body_lemma:{query_str}")
        else:
            args.append(query_str)

        if work_filter: args.extend(["--work", work_filter])
        if vol_filter: args.extend(["--volume", vol_filter])
        args.extend(["--context", str(context_width), "--limit", str(limit_val)])
        if include_footnotes: args.append("--footnotes")
            
        query_parts, options = sc.parse_args(args)
        query_info = sc.parse_query(query_parts)
        if use_lemma and query_info: query_info["terms"] = [query_str]
        
        if query_info:
            try:
                results = sc.search_database(sc.DEFAULT_DATABASE, query_info, options)
                st.success(f"Gefunden: {len(results)}.")
                for index, row in enumerate(results):
                    fn_marker = f" *(Fußnote {row.get('footnote_number', '')})*" if row.get('footnote_number') else ""
                    with st.expander(f"SW {row['sw_page_label']}{fn_marker} (PDF: {row['pdf_pages']})"):
                        col_btn, col_path = st.columns([1, 4])
                        with col_btn:
                            if st.button(f"Zum Text", key=f"read_{row['id']}_{index}"):
                                st.session_state.reader_mode = 'single_page'
                                st.session_state.reader_page = row['sw_page_label']
                                st.session_state.app_mode = "原文"
                                st.rerun()
                        with col_path:
                            if row.get("work_title"):
                                st.markdown(f"** {row.get('work_title')}**")
                                
                        st.markdown("---")
                        body_text = row["body"] if show_raw else sc.apply_corrections(row["body"], corrections)
                        snippet = sc.make_snippet(body_text, query_info, options["context"])
                        for target in sc.query_search_targets(query_info):
                            snippet = re.sub(f"({re.escape(target)})", r"**\1**", snippet, flags=re.IGNORECASE)
                        st.markdown(snippet)
            except Exception as e:
                st.error(f"Fehler: {e}")

elif app_mode == "原文":
    col_toc, col_reader = st.columns([1, 3])
    
    with col_toc:
        st.markdown("### Navigation")
        toc_tree = load_toc()
        
        selected_div = st.radio("Abtheilung (部)", ["I", "II"], horizontal=True)
        
        vols_dict = toc_tree.get(selected_div, {})
        vols_list = sorted(vols_dict.keys())
        if not vols_list:
            st.warning("Keine Daten")
        else:
            selected_vol = st.selectbox("Band (卷)", vols_list, format_func=lambda x: f"Band {x}")
            works_list = vols_dict.get(selected_vol, [])
            selected_work = st.selectbox("Werk (著作)", works_list)
            
            if st.button("加载", type="primary", width="stretch"):
                st.session_state.reader_mode = 'continuous'
                st.session_state.reader_nav = {
                    'div': selected_div,
                    'vol': selected_vol,
                    'work': selected_work
                }
                st.rerun()
            
        st.markdown("---")
        st.markdown("##### Einzelseite (单页)")
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            manual_page = st.text_input("SW", value=st.session_state.reader_page, label_visibility="collapsed")
        with col_m2:
            if st.button("Go"):
                st.session_state.reader_mode = 'single_page'
                st.session_state.reader_page = manual_page.strip()
                st.rerun()

    with col_reader:
        mode = st.session_state.reader_mode
        
        with st.container(height=850, border=True):
            if mode == 'single_page':
                col_p, col_n = st.columns(2)
                with col_p:
                    if st.button("⬅ Zurück", width="stretch"):
                        change_page(-1)
                        st.rerun()
                with col_n:
                    if st.button("Weiter ➡", width="stretch"):
                        change_page(1)
                        st.rerun()
                st.markdown("---")
                
                page_label = st.session_state.reader_page
                page, fns = sp.get_page(sc.DEFAULT_DATABASE, page_label)
                if page is None:
                    st.warning(f"Nicht gefunden: {page_label}")
                else:
                    if page.get("work_title"):
                        st.markdown(f"**📍 {page.get('work_title')}**")
                    render_page_block(page, fns, show_raw)
                            
            elif mode == 'continuous':
                nav = st.session_state.reader_nav
                st.markdown(f"## {nav['work']}")
                st.markdown("---")
                
                pages, fns = get_continuous_pages(sc.DEFAULT_DATABASE, nav['div'], nav['vol'], nav['work'])
                if not pages:
                    st.warning("Keine Texte gefunden.")
                else:
                    for p in pages:
                        page_fns = [fn for fn in fns if fn['page_id'] == p['id']]
                        render_page_block(p, page_fns, show_raw)

elif app_mode == "词汇统计":
    st.title("词汇统计")
    work_filter = st.selectbox("Werk (著作)", [""] + available_works)
    col_w, col_f1, col_f2 = st.columns([2, 1, 1])
    with col_w:
        word = st.text_input("Wort (词汇)", value="grund")
    with col_f1:
        use_lemma = st.checkbox("Lemmatisierung", value=True)
    with col_f2:
        filter_stop = st.checkbox("Stoppwörter filtern", value=True)
    
    if st.button("Analysieren", type="primary"):
        target_word = word.lower()
        connection = sqlite3.connect(sc.DEFAULT_DATABASE)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        
        query_sql = """
            SELECT pages.division, pages.volume, pages.sw_page_label, pages.body, pages.body_lemma, pages.work_title 
            FROM pages_fts 
            JOIN pages ON pages.rowid = pages_fts.rowid 
            WHERE pages_fts MATCH ?
        """
        params = [f"body_lemma:{target_word}" if use_lemma else f'"{target_word}"']
        if work_filter:
            query_sql += " AND pages.work_title = ?"
            params.append(work_filter)
            
        cursor.execute(query_sql, params)
        results = [dict(r) for r in cursor.fetchall()]
        connection.close()

        if not results:
            st.warning(f"Nicht gefunden: {word}")
        else:
            total_matches = 0
            position_counter = Counter({"Satzanfang": 0, "Satzmitte/-ende": 0})
            left_1_counter = Counter()
            right_1_counter = Counter()
            volume_data = defaultdict(lambda: {"total": 0})
            kwic_records = []
            
            for row in results:
                body = row["body"]
                body_lemma = row["body_lemma"]
                if not show_raw:
                    body = sc.apply_corrections(body, corrections)
                    
                vol_key = f"{row['division']},{row['volume']}"
                label = row["sw_page_label"]
                breadcrumb = row.get("work_title", "")
                
                sentences = split_sentences(body)
                lemmas = split_sentences(body_lemma) if body_lemma else []
                
                for i_s, sentence in enumerate(sentences):
                    words = get_words(sentence)
                    if use_lemma and i_s < len(lemmas):
                        l_words = get_words(lemmas[i_s])
                        indices = [i for i, w in enumerate(l_words) if w == target_word]
                    else:
                        indices = [i for i, w in enumerate(words) if w == target_word]
                        
                    for idx in indices:
                        if idx >= len(words): continue
                        total_matches += 1
                        volume_data[vol_key]["total"] += 1
                        
                        if idx < 3: position_counter["Satzanfang"] += 1
                        else: position_counter["Satzmitte/-ende"] += 1
                            
                        if idx > 0:
                            l_word = words[idx - 1]
                            if not (filter_stop and l_word in STOP_WORDS):
                                left_1_counter[l_word] += 1
                        if idx < len(words) - 1:
                            r_word = words[idx + 1]
                            if not (filter_stop and r_word in STOP_WORDS):
                                right_1_counter[r_word] += 1
                                
                        left_ctx = " ".join(words[max(0, idx-6):idx])
                        right_ctx = " ".join(words[idx+1:min(len(words), idx+7)])
                        kwic_records.append({
                            "SW": label,
                            "Werk": breadcrumb,
                            "L-Kontext": left_ctx,
                            "KW": words[idx],
                            "R-Kontext": right_ctx
                        })

            st.success(f"Treffer: {total_matches}")
            st.markdown("### 1. Verteilung (Band)")
            sorted_vols = sorted(volume_data.keys(), key=sort_volume_key)
            period_df = pd.DataFrame([{"Band": v, "Häufigkeit": volume_data[v]["total"]} for v in sorted_vols]).set_index("Band")
            st.bar_chart(period_df)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 2. Kollokationen")
                st.write("**L1 (Vorhergehend) Top 5**")
                st.dataframe(pd.DataFrame([{"Wort": k, "Häufigkeit": v} for k, v in left_1_counter.most_common(5)]), width="stretch")
            with col2:
                st.markdown("### 3. Syntax-Position")
                st.dataframe(pd.DataFrame([{"Position": k, "Häufigkeit": v, "Prozent": f"{(v/total_matches)*100:.1f}%"} for k, v in position_counter.items()]), width="stretch")

            st.markdown("### 4. KWIC-Index")
            if kwic_records:
                st.dataframe(pd.DataFrame(kwic_records), width="stretch", height=400)
                