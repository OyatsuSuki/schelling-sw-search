# Schelling Sämmtliche Werke Search

一个面向谢林（F. W. J. Schelling）研究的本地全文检索与原著阅读工具。

本项目将 **Schellings Sämmtliche Werke (SW)** 整理为可检索的文本语料库，并以 SQLite + SQLite FTS + Streamlit 提供一个轻量的研究界面。它的目标不是做一个通用的文献管理器，而是尽可能方便地回答谢林研究中最朴素、也最经常出现的问题：

> **某个词在哪里出现？它在不同著作、不同卷册中的使用情况如何？它附近通常出现什么？这一页原文究竟是什么？**

## Features

### 🔎 全文搜索

- 基于 SQLite FTS 的全文检索
- 支持单词、多个词和短语搜索
- 可按著作、卷册和页码范围筛选
- 可调整检索结果上下文长度与结果数量
- 支持选择是否搜索脚注
- 显示 SW 页码、著作和卷册信息

### 📖 原文阅读

- 按 SW 的卷册与著作结构浏览
- 支持直接输入 SW 页码跳转
- 提供上一页 / 下一页连续阅读
- 搜索结果可以直接跳转到对应原文页面
- 对已知的 PDF / OCR 文本错误应用校正表

### 📊 词汇与语料分析

- 统计词语在语料库中的出现情况
- KWIC（Key Word in Context）上下文查看
- 左右邻接词统计
- 按卷册观察词汇分布
- 支持基础的 lemma matching
- 使用 spaCy 德语模型进行词汇分析

## Corpus

当前语料库以 **Schellings Sämmtliche Werke** 为核心，经过文本解析、页码映射、结构化和校正后存储。

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

依赖已经列在 `requirements.txt` 中。fileciteturn3file0

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

## Design Philosophy

这个项目首先服务于哲学研究，而不是机器学习 benchmark。

因此语料库的基本单位不是抽象的 token，而是 **SW 页码 + 著作结构 + 原文**。这样做的目的，是让检索结果能够重新回到谢林著作的实际文本位置，而不是停留在一个无法核对出处的词频表中。

同时，项目保留了原始语料与校正机制之间的区分：文本校正通过独立的 JSON 文件应用，而不是直接把所有修改永久写死在检索代码里。fileciteturn6file0

## Status

这是一个正在持续完善的个人研究工具。

目前的重点是：

- 提高 SW 文本解析与校正质量
- 完善著作 / 卷册 / 页码层级
- 改进德语词形与 lemma 检索
- 增加更可靠的词汇、句法和共现分析
- 逐步将它发展为一个真正适合谢林研究的数字文本工作台

## License

代码部分的许可证见仓库中的 LICENSE（如果项目尚未提供 LICENSE，请在正式发布前补充）。

对于语料数据，请单独遵守其来源版本的版权与再分发条件。

## Acknowledgements

本项目主要用于 Friedrich Wilhelm Joseph Schelling 的德语原著研究。

如果这个工具对你的谢林研究有帮助，欢迎提交 Issue 或 Pull Request，尤其是：

- 文本错误与页码错误
- 著作结构错误
- 检索 bug
- 德语词形 / lemma 处理问题
- 对研究功能的建议
