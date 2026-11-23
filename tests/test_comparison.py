import io
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pls_compare


def _docx_bytes(clause_lines):
    doc = Document()
    for heading, body in clause_lines:
        doc.add_paragraph(heading)
        doc.add_paragraph(body)
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def test_extract_and_compare_demo_documents():
    root = Path(__file__).resolve().parents[1]
    result = pls_compare.compare(
        root / "data/Corporate_Agreement_Version_A_50pp.docx",
        root / "data/Corporate_Agreement_Version_B_50pp.docx",
    )
    assert result["version_a_clauses"] >= 45
    assert result["version_b_clauses"] >= 45
    assert result["changed_clauses"] >= 10
    assert "change_type_counts" in result


def test_modality_detects_must_vs_should():
    assert pls_compare.modality("Provider must notify Customer") != pls_compare.modality("Provider should notify Customer")


def test_added_removed_classification():
    assert pls_compare.classify(None, {"text": "new", "title": "x"}) == ["added"]
    assert pls_compare.classify({"text": "old", "title": "x"}, None) == ["removed"]


def test_compare_reports_inserted_and_removed_clauses_and_word_diff():
    a = _docx_bytes([("CLS-001 — Notice", "Provider must notify the customer within 10 days.")])
    b = _docx_bytes([
        ("CLS-001 — Notice", "Provider should notify the customer within 20 days."),
        ("CLS-002 — Audit", "Customer may inspect records."),
    ])
    result = pls_compare.compare(a, b)
    assert result["added_clauses"] == 1
    assert result["edited_clauses"] == 1
    changed = next(row for row in result["changes"] if row["clause_id"] == "CLS-001")
    assert "modality_changed" in changed["change_types"]
    assert "temporal_expression_changed" in changed["change_types"]
    assert {segment["type"] for segment in changed["diff"]} == {"removed", "added"}


def test_title_only_change_is_detected():
    old = {"title": "Payment", "text": "No change."}
    new = {"title": "Payment and Fees", "text": "No change."}
    assert pls_compare.classify(old, new) == ["title_changed"]


def test_extract_document_routes_docx_bytes():
    payload = _docx_bytes([("CLS-010 — Confidentiality", "Recipient must protect the information.")])
    clauses = pls_compare.extract_document(payload)
    assert "CLS-010" in clauses


def test_extract_pdf_text_layer():
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "CLS-021 — Liability")
    page.insert_text((72, 100), "Supplier must maintain adequate insurance.")
    payload = pdf.tobytes()
    pdf.close()
    clauses = pls_compare.extract_document(payload)
    assert clauses["CLS-021"]["title"] == "Liability"
    assert "adequate insurance" in clauses["CLS-021"]["text"]
