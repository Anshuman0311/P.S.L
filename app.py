"""Streamlit frontend for P.L.S. clause-level document comparison."""
from __future__ import annotations

import html
import io
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import pls_compare  # noqa: E402

st.set_page_config(
    page_title="P.L.S. | Legal Change Review",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap');
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      .stApp { background: #f5f7fb; }
      .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 4rem; }
      .hero { background: linear-gradient(125deg,#101b35 0%,#203b67 100%); color: white; border-radius: 20px; padding: 30px 34px; margin-bottom: 24px; }
      .eyebrow { font-family: 'DM Mono', monospace; letter-spacing: .16em; text-transform: uppercase; font-size: 11px; color: #a9c4f3; }
      .hero h1 { font-size: clamp(30px,4vw,44px); letter-spacing: -.04em; margin: 10px 0 8px 0; color: white; }
      .hero p { color: #d7e2f5; font-size: 15px; margin: 0; max-width: 760px; }
      .metric { background: white; border: 1px solid #e3e8f0; border-radius: 15px; padding: 17px 19px; min-height: 105px; }
      .metric-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .07em; }
      .metric-value { font-size: 30px; line-height: 1.25; font-weight: 800; color: #17233b; margin-top: 5px; }
      .section-title { color: #17233b; font-size: 20px; font-weight: 800; margin: 12px 0 4px 0; }
      .muted { color: #64748b; font-size: 13px; }
      .tag { display:inline-block; border-radius:999px; padding:4px 9px; margin:2px 4px 2px 0; background:#edf2fa; color:#334968; font:11px 'DM Mono',monospace; }
      .tag-risk { background:#fff0e8; color:#9a3412; }
      .diff { white-space:pre-wrap; line-height:1.8; font-size:13px; color:#334155; background:white; border:1px solid #e2e8f0; border-radius:10px; padding:12px; overflow-wrap:anywhere; }
      .diff del { background:#ffe1e1; color:#9f2525; text-decoration:line-through; padding:1px 2px; border-radius:3px; }
      .diff ins { background:#dcfce7; color:#166534; text-decoration:none; padding:1px 2px; border-radius:3px; }
      .smallcaps { font:11px 'DM Mono',monospace; color:#64748b; text-transform:uppercase; letter-spacing:.09em; }
      .notice { border:1px solid #f2d7a2; background:#fff9eb; color:#76521a; border-radius:12px; padding:13px 15px; font-size:13px; }
      [data-testid="stFileUploader"] { background:white; border:1px dashed #bcc9dc; border-radius:14px; padding:8px; }
      div[data-testid="stExpander"] { background:white; border:1px solid #e2e8f0; border-radius:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">P.L.S. · POLICY & LEGAL SHIFT</div>
      <h1>See what changed.<br>Understand where to look.</h1>
      <p>Compare two versions of a Word agreement, surface clause-level changes, and inspect the exact wording that was removed or introduced.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Review settings")
    st.caption("P.L.S. analyses .docx and text-based .pdf files with clause IDs such as CLS-001.")
    st.divider()
    st.markdown("**Detected signals**")
    st.caption("Obligation / permission wording")
    st.caption("Negation and prohibition signals")
    st.caption("Deadlines and time expressions")
    st.caption("Added, removed, and edited clauses")
    st.divider()
    st.markdown("**Review boundary**")
    st.caption("This is a deterministic prototype. It flags candidate changes; it does not decide legal effect or provide legal advice.")

left, right = st.columns(2, gap="large")
with left:
    st.markdown("<div class='section-title'>01 / Earlier version</div>", unsafe_allow_html=True)
    file_a = st.file_uploader("Upload the earlier agreement", type=["docx", "pdf"], key="version_a")
with right:
    st.markdown("<div class='section-title'>02 / Later version</div>", unsafe_allow_html=True)
    file_b = st.file_uploader("Upload the revised agreement", type=["docx", "pdf"], key="version_b")

run = st.button("Compare both versions  →", type="primary", use_container_width=True, disabled=not (file_a and file_b))

if run:
    try:
        with st.spinner("Reading clauses and comparing versions…"):
            result = pls_compare.compare(file_a, file_b)
        if result["version_a_clauses"] == 0 and result["version_b_clauses"] == 0:
            st.error("No recognised clauses were found. Add clause headings in the format CLS-001 — Heading and try again.")
            st.stop()
        st.session_state["pls_result"] = result
        st.session_state["pls_names"] = (file_a.name, file_b.name)
    except Exception as exc:
        st.error(f"Could not compare these files: {exc}")
        st.info("Check that both files are valid, unencrypted .docx or text-based .pdf documents. PDF support also requires PyMuPDF.")

result = st.session_state.get("pls_result")
if result:
    names = st.session_state.get("pls_names", ("Version A", "Version B"))
    st.divider()
    st.markdown("<div class='section-title'>Comparison overview</div>", unsafe_allow_html=True)
    st.caption(f"{names[0]}  →  {names[1]}")
    metrics = [
        ("Clauses in earlier", result["version_a_clauses"]),
        ("Clauses in later", result["version_b_clauses"]),
        ("Changed clauses", result["changed_clauses"]),
        ("Added / removed", f"{result['added_clauses']} / {result['removed_clauses']}"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(f"<div class='metric'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)

    summary_left, summary_right = st.columns([1.3, 1], gap="large")
    with summary_left:
        st.markdown("<div class='section-title'>Change signals</div>", unsafe_allow_html=True)
        counts = result.get("change_type_counts", {})
        if counts:
            chart_data = {key.replace("_", " ").title(): value for key, value in counts.items()}
            st.bar_chart(chart_data)
        else:
            st.success("No clause-level changes were detected by the current rules.")
    with summary_right:
        st.markdown("<div class='section-title'>Export findings</div>", unsafe_allow_html=True)
        json_bytes = json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8")
        csv_buffer = io.StringIO()
        pls_compare.write_csv(result, csv_buffer)
        st.download_button("Download full report · JSON", json_bytes, file_name="pls_comparison.json", mime="application/json", use_container_width=True)
        st.download_button("Download findings · CSV", csv_buffer.getvalue().encode("utf-8"), file_name="pls_findings.csv", mime="text/csv", use_container_width=True)

    st.divider()
    st.markdown("<div class='section-title'>Clause-by-clause findings</div>", unsafe_allow_html=True)
    st.caption("Search by clause ID or wording. Filter by detected signal to focus the review.")
    all_changes = result["changes"]
    available_tags = sorted({tag for row in all_changes for tag in row["change_types"]})
    filter_col, search_col, risk_col = st.columns([1.1, 1.5, 1])
    with filter_col:
        selected_tags = st.multiselect("Change type", available_tags, default=available_tags)
    with search_col:
        search_text = st.text_input("Search findings", placeholder="e.g. CLS-012, termination, payment…")
    with risk_col:
        only_shift = st.checkbox("Possible weakening only", value=False)

    filtered = []
    query = search_text.strip().lower()
    for row in all_changes:
        tags = set(row["change_types"])
        haystack = " ".join(str(row.get(k) or "") for k in ("clause_id", "title", "title_a", "title_b", "version_a", "version_b")).lower()
        if selected_tags and not tags.intersection(selected_tags):
            continue
        if query and query not in haystack:
            continue
        if only_shift and "possible_weakening" not in tags:
            continue
        filtered.append(row)

    st.caption(f"Showing {len(filtered)} of {len(all_changes)} flagged clauses")
    if not filtered:
        st.info("No findings match these filters.")

    for row in filtered:
        tags = row["change_types"]
        badge_html = "".join(
            f"<span class='tag {'tag-risk' if tag == 'possible_weakening' else ''}'>{html.escape(tag.replace('_', ' '))}</span>"
            for tag in tags
        )
        heading = f"{row['clause_id']}  ·  {row['title']}"
        with st.expander(heading, expanded=False):
            st.markdown(badge_html, unsafe_allow_html=True)
            if row.get("version_a") is not None and row.get("version_b") is not None:
                diff_html = "".join(
                    f"<del>{html.escape(seg['text'])}</del>" if seg["type"] == "removed" else f"<ins>{html.escape(seg['text'])}</ins>"
                    for seg in row.get("diff", [])
                )
                if diff_html:
                    st.markdown("<div class='smallcaps'>Changed wording · red = removed / green = added</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='diff'>{diff_html}</div>", unsafe_allow_html=True)
                old_col, new_col = st.columns(2, gap="medium")
                with old_col:
                    st.markdown("**Earlier version**")
                    st.text(row.get("version_a") or "")
                with new_col:
                    st.markdown("**Revised version**")
                    st.text(row.get("version_b") or "")
            elif row.get("version_a") is None:
                st.markdown("**New clause in the later version**")
                st.text(row.get("version_b") or "")
            else:
                st.markdown("**Clause removed from the later version**")
                st.text(row.get("version_a") or "")

    st.markdown(
        "<div class='notice'><b>Important:</b> A detected shift is a review signal, not a legal conclusion. The current parser recognises clauses with stable IDs (CLS-###) in the body text of Word documents or selectable PDF text. It does not OCR scanned/image-only PDFs, analyse headers/footers, comments, tracked changes, image text, or semantically align clauses when IDs change. Have a qualified reviewer assess material findings.</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown("""
    <div style="background:white;border:1px solid #e3e8f0;border-radius:16px;padding:22px;margin-top:18px">
      <div class="smallcaps">Your review workspace</div>
      <div style="font-size:18px;font-weight:700;color:#17233b;margin:8px 0">Upload two versions to begin</div>
      <div class="muted">P.L.S. will extract recognised clauses, align stable clause IDs, and show where the wording differs.</div>
    </div>
    """, unsafe_allow_html=True)
