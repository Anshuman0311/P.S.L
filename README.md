# P.L.S. — Legal Document Change Detection

**P.L.S. (Policy & Legal Shift)** is an explainable, clause-level demonstrator for reviewing two versions of a Word agreement. It provides both a command-line interface and a browser-based upload-and-compare workspace.

## Run the web interface

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, upload the **earlier** and **revised** `.docx` or text-based `.pdf` files, and select **Compare both versions**. The workspace shows an overview, change-signal counts, clause-level results, removed/added wording, filters, search, and JSON/CSV downloads.

## Run from the command line

```bash
python src/pls_compare.py data/Corporate_Agreement_Version_A_50pp.docx data/Corporate_Agreement_Version_B_50pp.docx --out outputs/comparison.json
pytest -q
```

## What it detects

- Clauses added or removed between versions, when clause IDs are present in only one version.
- Edits within matching clause IDs, including title-only changes.
- Candidate shifts in modal language (for example, *must*, *may*, *should*), negation/prohibition signals, and explicit time expressions.
- Word-level additions and removals to help a reviewer locate the exact changed wording.

Every finding preserves the original and revised clause text as evidence. Results can be exported as JSON or CSV.

## Input and alignment scope

- **Supported input:** `.docx` Word documents and text-based `.pdf` documents (selectable text).
- **Clause format:** a heading beginning with a stable identifier such as `CLS-001 — Notices`.
- Word paragraphs and tables in the document body are read; selectable PDF page text is also read.
- Matching is based on stable clause IDs, not deep semantic alignment.

## Limitations and responsible use

This is a deterministic prototype, not a validated legal AI system. It does **not** OCR scanned/image-only PDFs or analyse image text, Word headers/footers, comments, tracked-change markup, or free-standing text outside recognised clauses. It may miss a clause when its ID is removed or changed, and its linguistic heuristics can produce false positives or false negatives. A label such as `possible_weakening` is a triage signal, not a legal conclusion. The tool does not determine enforceability, breach, liability, or provide legal advice. A qualified human reviewer must assess material findings.

## Demonstration corpus

`data/Corporate_Agreement_Version_A_50pp.docx` and `data/Corporate_Agreement_Version_B_50pp.docx` are fictional synthetic documents for controlled demonstration. They are not real contracts and must not be relied upon.

## Windows quick launch

Double-click `RUN_PLS.bat`. It installs the listed Python dependencies and starts the local web app. The first run requires an internet connection to install Streamlit and PyMuPDF if they are not already installed.
