# Schelling Sämmtliche Werke

A search tool for Schelling's Sämmtliche Werke (SW).

This project organizes the Schelling SW into a searchable text corpus and provides a lightweight interface using SQLite + SQLite FTS + Streamlit.

## Features

- Full-text search
- Read original pages
- Word frequency statistics

## Corpus

Main data files:

```text
corpus/
├── database/
│   └── schelling.db
└── processed/
    └── schelling/
        └── sw_pages.jsonl
```

The SQLite database stores structured page data for search and reading; `sw_pages.jsonl` contains the processed page-level corpus.

> **Copyright note:** The project's code and corpus-processing methods can be shared publicly, but whether the SW text data in this repository may be redistributed depends on the copyright and licensing of the specific source/version used. Please check the source/version license before redistributing any text data.

## Requirements

- Python 3.10+ (use a virtual environment recommended)
- Streamlit
- pandas
- spaCy
- German spaCy model `de_core_news_sm`

Dependencies are listed in `requirements.txt`.

## Installation

Clone the repository:

```bash
git clone https://github.com/OyatsuSuki/schelling-sw-search.git
cd schelling-sw-search
```

Create a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Start Streamlit:

```bash
streamlit run src/app.py
```

Then open the local address Streamlit provides in your browser.

## Project Structure

```text
schelling-sw-search/
│
├── src/
│   ├── app.py                  # Streamlit main UI
│   ├── search_corpus.py        # Full-text search, query parsing, and text corrections
│   └── show_page.py            # Original page display
│
├── corpus/
│   ├── database/
│   │   └── schelling.db        # SQLite database
│   └── processed/
│       └── schelling/
│           └── sw_pages.jsonl  # Processed page corpus
│
├── data/
│   └── schelling_ocr_corrections.json
│
├── requirements.txt
└── README.md
```

The application entry point is `src/app.py`. The search module uses `corpus/database/schelling.db` as the default database and reads text corrections from the corrections file.

## Search Syntax

Basic searches accept single words:

```text
Freiheit
```

You can search multiple words or phrases. Input with spaces can be treated as a phrase, for example:

```text
absolute Freiheit
```

Exact phrases can be quoted:

```text
"absolute Freiheit"
```

The search UI also allows filtering by work, volume, page range, context length, and number of results.

## Status

This is an ongoing personal research tool.

Current priorities:

- Improve SW text parsing and corrections
- Refine work/volume/page hierarchy
- Improve German lemmatization and morphological search
- Add more robust lexical, syntactic, and co-occurrence analyses

## License

For corpus data, please follow the copyright and redistribution terms of the data source/version used.

## Acknowledgements

This project is intended for research on Friedrich Wilhelm Joseph Schelling's German works.

If this tool is useful to you, feel free to open an Issue or submit a Pull Request.
