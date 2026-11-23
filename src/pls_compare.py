"""P.L.S.: explainable clause-level comparison for Word agreements.

This is a deterministic demonstration tool, not a legal decision system.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import re
from pathlib import Path
from typing import Any, BinaryIO

from docx import Document
from docx.document import Document as DocumentObject
from docx.table import Table
from docx.text.paragraph import Paragraph

MODALS = {
    "must": "strong_obligation",
    "shall": "strong_obligation",
    "is required to": "strong_obligation",
    "will": "commitment",
    "should": "recommendation",
    "may": "permission",
    "can": "permission",
    "is entitled to": "right",
    "is prohibited from": "prohibition",
    "must not": "prohibition",
    "shall not": "prohibition",
    "may not": "prohibition",
    "cannot": "prohibition",
}
TIME_RE = re.compile(
    r"\b(\d+\s+(?:calendar\s+days?|business\s+days?|days?|months?|years?|hours?))\b",
    re.I,
)
NEG_RE = re.compile(r"\b(not|no|never|without|prohibited|exclude[ds]?)\b", re.I)
CLAUSE_RE = re.compile(r"^(CLS-\d{3})\s+[\-‐‑‒–—−·•]\s+(.+)$", re.I)
TOKEN_RE = re.compile(r"\w+|[^\w\s]+|\s+", re.UNICODE)


def _iter_blocks(parent: DocumentObject):
    """Yield paragraphs and tables in the order they occur in the DOCX body."""
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P

    body = parent.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def _block_text(block: Any) -> list[str]:
    if isinstance(block, Paragraph):
        text = " ".join(block.text.split())
        return [text] if text else []
    rows = []
    for row in block.rows:
        cells = [" ".join(cell.text.split()) for cell in row.cells]
        row_text = " | ".join(value for value in cells if value)
        if row_text:
            rows.append(row_text)
    return rows


def _clauses_from_text_blocks(blocks: list[str]) -> dict[str, dict[str, str]]:
    clauses: dict[str, dict[str, str]] = {}
    current_id: str | None = None
    for text in blocks:
        text = " ".join(text.split())
        if not text:
            continue
        match = CLAUSE_RE.match(text)
        if match:
            current_id = match.group(1).upper()
            if current_id not in clauses:
                clauses[current_id] = {"title": match.group(2).strip(), "text": ""}
            else:
                clauses[current_id]["text"] += " " + match.group(2).strip()
            continue
        if current_id and not text.startswith("NS-MRG"):
            existing = clauses[current_id]["text"]
            if len(existing) < 20000:
                clauses[current_id]["text"] = (existing + " " + text).strip()
    return clauses


def extract_docx(source: str | Path | BinaryIO | bytes) -> dict[str, dict[str, str]]:
    """Extract stable-ID clauses from paragraphs and tables in a DOCX body."""
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    doc = Document(source)
    blocks: list[str] = []
    for block in _iter_blocks(doc):
        blocks.extend(_block_text(block))
    return _clauses_from_text_blocks(blocks)


def extract_pdf(source: str | Path | BinaryIO | bytes) -> dict[str, dict[str, str]]:
    """Extract selectable text from a PDF; scanned/image-only PDFs are not OCRed."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError("PDF input requires PyMuPDF. Install it with: pip install pymupdf") from exc

    if isinstance(source, bytes):
        data = source
    elif hasattr(source, "getvalue"):
        data = source.getvalue()
    elif hasattr(source, "read"):
        position = source.tell() if hasattr(source, "tell") else None
        if hasattr(source, "seek"):
            source.seek(0)
        data = source.read()
        if position is not None and hasattr(source, "seek"):
            source.seek(position)
    else:
        data = Path(source).read_bytes()

    blocks: list[str] = []
    with fitz.open(stream=data, filetype="pdf") as pdf:
        for page in pdf:
            blocks.extend(page.get_text("text", sort=True).splitlines())
    return _clauses_from_text_blocks(blocks)


def extract_document(source: str | Path | BinaryIO | bytes) -> dict[str, dict[str, str]]:
    """Extract clauses from a .docx or text-based .pdf source."""
    name = getattr(source, "name", "")
    suffix = Path(str(name or source)).suffix.lower() if not isinstance(source, bytes) else ""
    if isinstance(source, bytes):
        data = source
    elif hasattr(source, "getvalue"):
        data = source.getvalue()
    elif hasattr(source, "read"):
        position = source.tell() if hasattr(source, "tell") else None
        if hasattr(source, "seek"):
            source.seek(0)
        data = source.read()
        if position is not None and hasattr(source, "seek"):
            source.seek(position)
    else:
        data = Path(source).read_bytes()
    if suffix == ".pdf" or data.startswith(b"%PDF"):
        return extract_pdf(data)
    return extract_docx(data)


def modality(text: str) -> list[tuple[str, str]]:
    low = text.lower()
    found = []
    for phrase, label in sorted(MODALS.items(), key=lambda item: -len(item[0])):
        if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", low):
            found.append((phrase, label))
    return found


def _strength(text: str) -> int:
    strengths = {
        "prohibition": 4,
        "strong_obligation": 3,
        "right": 2,
        "commitment": 2,
        "permission": 1,
        "recommendation": 0,
    }
    return max((strengths.get(label, 0) for _, label in modality(text)), default=0)


def classify(old: dict[str, str] | None, new: dict[str, str] | None) -> list[str]:
    if old is None:
        return ["added"]
    if new is None:
        return ["removed"]

    tags: list[str] = []
    old_text, new_text = old.get("text", ""), new.get("text", "")
    if old.get("title", "") != new.get("title", ""):
        tags.append("title_changed")
    if old_text != new_text:
        tags.append("text_changed")
        old_modals, new_modals = modality(old_text), modality(new_text)
        if old_modals != new_modals:
            tags.append("modality_changed")
        if bool(NEG_RE.search(old_text)) != bool(NEG_RE.search(new_text)):
            tags.append("negation_signal_changed")
        if TIME_RE.findall(old_text) != TIME_RE.findall(new_text):
            tags.append("temporal_expression_changed")
        old_strength, new_strength = _strength(old_text), _strength(new_text)
        if old_strength > new_strength:
            tags.append("possible_weakening")
        elif new_strength > old_strength:
            tags.append("possible_strengthening")
    return tags or ["unchanged"]


def word_diff(old_text: str, new_text: str) -> list[dict[str, str]]:
    """Return changed word/punctuation segments; unchanged spans are omitted."""
    old_tokens, new_tokens = TOKEN_RE.findall(old_text), TOKEN_RE.findall(new_text)
    matcher = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    segments: list[dict[str, str]] = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            continue
        if op in ("replace", "delete"):
            value = "".join(old_tokens[i1:i2])
            if value:
                segments.append({"type": "removed", "text": value})
        if op in ("replace", "insert"):
            value = "".join(new_tokens[j1:j2])
            if value:
                segments.append({"type": "added", "text": value})
    return segments


def compare(a_source: Any, b_source: Any) -> dict[str, Any]:
    a, b = extract_document(a_source), extract_document(b_source)
    results = []
    for clause_id in sorted(set(a) | set(b)):
        old, new = a.get(clause_id), b.get(clause_id)
        tags = classify(old, new)
        if tags == ["unchanged"]:
            continue
        results.append(
            {
                "clause_id": clause_id,
                "title": (new or old)["title"],
                "title_a": old["title"] if old else None,
                "title_b": new["title"] if new else None,
                "change_types": tags,
                "version_a": old["text"] if old else None,
                "version_b": new["text"] if new else None,
                "diff": word_diff(old["text"], new["text"]) if old and new else [],
            }
        )

    added = sum("added" in row["change_types"] for row in results)
    removed = sum("removed" in row["change_types"] for row in results)
    edited = sum(
        not ({"added", "removed"} & set(row["change_types"])) for row in results
    )
    type_counts: dict[str, int] = {}
    for row in results:
        for tag in row["change_types"]:
            type_counts[tag] = type_counts.get(tag, 0) + 1

    return {
        "version_a_clauses": len(a),
        "version_b_clauses": len(b),
        "changed_clauses": len(results),
        "added_clauses": added,
        "removed_clauses": removed,
        "edited_clauses": edited,
        "change_type_counts": dict(sorted(type_counts.items())),
        "changes": results,
    }


def write_csv(result: dict[str, Any], destination: str | Path | io.StringIO) -> None:
    fields = ["clause_id", "title", "change_types", "version_a", "version_b"]
    should_close = not hasattr(destination, "write")
    handle = open(destination, "w", newline="", encoding="utf-8") if should_close else destination
    try:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in result["changes"]:
            writer.writerow(
                {
                    **{key: row.get(key) for key in fields if key != "change_types"},
                    "change_types": ";".join(row["change_types"]),
                }
            )
    finally:
        if should_close:
            handle.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two Word or text-based PDF agreement versions")
    parser.add_argument("version_a")
    parser.add_argument("version_b")
    parser.add_argument("--out", default="comparison.json")
    args = parser.parse_args()
    result = compare(args.version_a, args.version_b)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(result, output.with_suffix(".csv"))
    print(json.dumps({key: value for key, value in result.items() if key != "changes"}, indent=2))


if __name__ == "__main__":
    main()
