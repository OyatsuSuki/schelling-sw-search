# Schelling Sämmtliche Werke

一个谢林SW搜索工具。

本项目将 **Schellings Sämmtliche Werke (SW)** 整理为可检索的文本语料库，以 SQLite + SQLite FTS + Streamlit 提供一个轻量的界面。

## Features

全文搜索

原文阅读

词汇统计

## Corpus

主要数据文件：

```text
corpus/
├── database/
│   └── schelling.db
└── processed/
    └── schelling/
        └── sw_pages.jsonl
```

SQLite 数据库保存用于检索和阅读的结构化页面数据；`sw_pages.jsonl` 保存处理后的页面级语料。

> **版权说明：** 本项目的软件代码与语料处理方法可以公开，但仓库中的 SW 文本数据是否可以再分发，取决于所使用版本的版权与授权状况。使用者应自行确认其所在地及具体版本的版权状态。本项目不主张对谢林原著本身拥有版权。

## Requirements

- Python 3.10+（建议使用虚拟环境）
- Streamlit
- pandas
- spaCy
- German spaCy model `de_core_news_sm`

依赖已经列在 `requirements.txt` 中。

## Installation

Clone repository：

```bash
git clone https://github.com/OyatsuSuki/schelling-sw-search.git
cd schelling-sw-search
```

创建虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

## Run

启动 Streamlit：

```bash
streamlit run src/app.py
```

然后在浏览器中打开 Streamlit 提供的本地地址。

## Project Structure

```text
schelling-sw-search/
│
├── src/
│   ├── app.py                  # Streamlit 主界面
│   ├── search_corpus.py        # 全文检索、查询解析与文本校正
│   └── show_page.py             # 原文页面显示
│
├── corpus/
│   ├── database/
│   │   └── schelling.db        # SQLite 数据库
│   └── processed/
│       └── schelling/
│           └── sw_pages.jsonl  # 处理后的页面语料
│
├── data/
│   └── schelling_ocr_corrections.json
│
├── requirements.txt
└── README.md
```

当前应用的入口是 `src/app.py`；检索模块使用 `corpus/database/schelling.db` 作为默认数据库，并从校正文件读取文本修正。fileciteturn5file0 fileciteturn6file0

## Search Syntax

最基本的搜索直接输入词语即可：

```text
Freiheit
```

也可以搜索多个词或短语。带空格的输入可以作为短语处理，例如：

```text
absolute Freiheit
```

精确短语可以使用引号：

```text
"absolute Freiheit"
```

搜索界面还可以进一步限定著作、卷册、页码范围、上下文长度和结果数量。

## Status

这是一个正在持续完善的个人研究工具。

目前的重点是：

- 提高SW文本解析与校正质量
- 完善著作/卷册/页码层级
- 改进德语词形与lemma检索
- 增加更可靠的词汇、句法和共现分析

## License

对于语料数据，请单独遵守其来源版本的版权与再分发条件。

## Acknowledgements

本项目主要用于 Friedrich Wilhelm Joseph Schelling 的德语原著研究。

如果这个工具对你有帮助，欢迎提交 Issue 或 Pull Request。
