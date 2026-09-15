import hashlib
import csv
import io

import matplotlib.pyplot as plt
import streamlit as st

from case_metadata import extract_case_date, extract_judge_and_court
from pdf_utils import extract_text_from_pdf
from summarizer import (
    detect_case_type,
    extract_case_title,
    extract_legal_issues,
    predict_case_outcome,
    split_summary,
    summarize_legal_text,
)

st.set_page_config(page_title="Legal Manager | Legal Intelligence", page_icon="⚖️", layout="wide")


def load_css():
    with open("styles.css", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def analyze_case(text, mode):
    outcome, confidence, uncertainty, evidence = predict_case_outcome(text)
    judge, court = extract_judge_and_court(text)
    return {
        "summary": summarize_legal_text(text, mode),
        "title": extract_case_title(text),
        "case_type": detect_case_type(text),
        "issues": extract_legal_issues(text),
        "outcome": outcome,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "evidence": evidence,
        "judge": judge,
        "court": court,
        "date": extract_case_date(text),
        "words": len(text.split()),
        "pages": max(1, round(len(text.split()) / 450)),
    }


def metric(label, value, detail, tone=""):
    st.markdown(
        f"<div class='metric-card {tone}'><div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value}</div><div class='metric-detail'>{detail}</div></div>",
        unsafe_allow_html=True,
    )


def report(data):
    issues = "\n- ".join(data["issues"] or ["Not explicitly detected"])
    return (f"LEXORA LEGAL INTELLIGENCE REPORT\n\nCase: {data['title']}\nType: {data['case_type']}\n"
            f"Court: {data['court']}\nJudge: {data['judge']}\nDate: {data['date']}\n"
            f"Disposition: {data['outcome']}\nConfidence: {data['confidence']}%\n\n"
            f"SUMMARY\n{data['summary']}\n\nEVIDENCE\n{data['evidence']}\n\nLEGAL ISSUES\n- {issues}").encode()


@st.cache_data(show_spinner=False)
def analyze_bulk_case(documents, mode):
    results = []
    for filename, text in documents:
        result = analyze_case(text, mode).copy()
        result["filename"] = filename
        result["document_key"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        results.append(result)
    return results


def bulk_csv(results):
    output = io.StringIO()
    fields = ["filename", "title", "case_type", "outcome", "confidence", "words", "pages", "issues", "court", "judge", "date"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for result in results:
        writer.writerow({
            "filename": result["filename"],
            "title": result["title"],
            "case_type": result["case_type"],
            "outcome": result["outcome"],
            "confidence": result["confidence"],
            "words": result["words"],
            "pages": result["pages"],
            "issues": len(result["issues"]),
            "court": result["court"],
            "judge": result["judge"],
            "date": result["date"],
        })
    return output.getvalue().encode("utf-8")


def count_values(results, key):
    counts = {}
    for result in results:
        value = result[key]
        counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


load_css()
st.session_state.setdefault("analysis", None)
st.session_state.setdefault("source_text", "")

with st.sidebar:
    st.markdown("<div class='brand'><b>⚡ Legal Manager</b><small>AI LEGAL OPS</small></div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-label'>WORKSPACE</div>", unsafe_allow_html=True)
    view = st.radio("Workspace", ["Dashboard", "Analyze case", "Bulk analyzer", "Case insights"], label_visibility="collapsed")
    st.markdown("<div class='sidebar-label'>ANALYSIS SPEED</div>", unsafe_allow_html=True)
    mode = st.select_slider("Summary mode", options=["Fast", "Balanced", "Detailed"], value="Fast")
    st.caption("Fast is instant and local. Transformer modes load only when selected.")
    st.markdown("<div class='sidebar-footer'>● SYSTEM READY<br><span>Evidence-first analysis</span></div>", unsafe_allow_html=True)

st.markdown("<div class='topbar'><span>LEGAL INTELLIGENCE WORKSPACE</span><b>● LIVE</b></div>", unsafe_allow_html=True)

if view == "Bulk analyzer":
    st.markdown("<div class='hero bulk-hero'><div><div class='eyebrow'>PORTFOLIO OPERATIONS / BATCH REVIEW</div><h1>See the pattern<br><em>across every case.</em></h1><p>Upload a folder of judgments and compare dispositions, case types, confidence, and review workload in one live workspace.</p></div><div class='hero-mark'>▦<small>02</small></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-heading'><span>BULK CASE INGESTION</span><small>Cached per document</small></div>", unsafe_allow_html=True)
    bulk_files = st.file_uploader("Upload multiple judgment PDFs", type="pdf", accept_multiple_files=True, help="Select one or more PDF judgments to analyze together.")
    bulk_action, bulk_clear = st.columns([1, 1])
    with bulk_action:
        bulk_clicked = st.button("Analyze case portfolio  →", type="primary", use_container_width=True)
    with bulk_clear:
        clear_bulk = st.button("Clear portfolio", use_container_width=True)
    if clear_bulk:
        st.session_state.bulk_results = None
        st.rerun()
    if bulk_clicked:
        if not bulk_files:
            st.warning("Upload at least one PDF to start the bulk analysis.")
        else:
            documents = tuple((file.name, extract_text_from_pdf(file)) for file in bulk_files)
            with st.spinner(f"Analyzing {len(documents)} case(s) in {mode.lower()} mode..."):
                st.session_state.bulk_results = analyze_bulk_case(documents, mode)
            st.success(f"Portfolio ready: {len(documents)} case(s) analyzed.")

    results = st.session_state.get("bulk_results")
    if results:
        disposition_filter, type_filter, confidence_filter = st.columns(3)
        dispositions = ["All dispositions"] + [value for value, _ in count_values(results, "outcome")]
        types = ["All case types"] + [value for value, _ in count_values(results, "case_type")]
        with disposition_filter:
            selected_disposition = st.selectbox("Disposition filter", dispositions)
        with type_filter:
            selected_type = st.selectbox("Case type filter", types)
        with confidence_filter:
            minimum_confidence = st.slider("Minimum evidence confidence", 0, 95, 0, 5)
        filtered = [
            result for result in results
            if (selected_disposition == "All dispositions" or result["outcome"] == selected_disposition)
            and (selected_type == "All case types" or result["case_type"] == selected_type)
            and result["confidence"] >= minimum_confidence
        ]
        st.markdown("<div class='section-heading'><span>PORTFOLIO SNAPSHOT</span><small>Filters update instantly</small></div>", unsafe_allow_html=True)
        cards = st.columns(5)
        avg_confidence = round(sum(result["confidence"] for result in filtered) / len(filtered), 1) if filtered else 0
        total_words = sum(result["words"] for result in filtered)
        with cards[0]: metric("Cases analyzed", len(filtered), f"of {len(results)} uploaded")
        with cards[1]: metric("Average confidence", f"{avg_confidence}%", "Evidence signal", "green")
        with cards[2]: metric("Total pages", sum(result["pages"] for result in filtered), "Estimated reading load", "blue")
        with cards[3]: metric("Review issues", sum(len(result["issues"]) for result in filtered), "Across filtered cases", "gold")
        with cards[4]: metric("Words processed", f"{total_words:,}", "Source text volume")

        if not filtered:
            st.info("No cases match the current filters.")
        else:
            chart_left, chart_right = st.columns(2)
            with chart_left:
                st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>OUTCOME MIX</div><h3>Disposition distribution</h3>", unsafe_allow_html=True)
                values = count_values(filtered, "outcome")
                fig, ax = plt.subplots(figsize=(7, 3.2))
                ax.barh([item[0] for item in values][::-1], [item[1] for item in values][::-1], color="#e8ad4e")
                ax.set_xlabel("Cases"); ax.spines[["top", "right", "left"]].set_visible(False); ax.grid(axis="x", linestyle="--", alpha=.25)
                st.pyplot(fig, use_container_width=True); plt.close(fig)
                st.markdown("</div>", unsafe_allow_html=True)
            with chart_right:
                st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>LEGAL MIX</div><h3>Case types in portfolio</h3>", unsafe_allow_html=True)
                values = count_values(filtered, "case_type")
                fig, ax = plt.subplots(figsize=(7, 3.2))
                ax.pie([item[1] for item in values], labels=[item[0].replace(" Case", "") for item in values], autopct="%1.0f%%", startangle=90, colors=["#315d83", "#e8ad4e", "#3b9a68", "#b9c3c9", "#d99e72"])
                ax.axis("equal")
                st.pyplot(fig, use_container_width=True); plt.close(fig)
                st.markdown("</div>", unsafe_allow_html=True)

            load_left, load_right = st.columns(2)
            with load_left:
                st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>QUALITY CONTROL</div><h3>Confidence spread</h3>", unsafe_allow_html=True)
                fig, ax = plt.subplots(figsize=(7, 3.2))
                confidence_values = [result["confidence"] for result in filtered]
                ax.hist(confidence_values, bins=[0, 50, 60, 70, 80, 90, 100], color="#315d83", edgecolor="white")
                ax.set_xlabel("Evidence confidence (%)"); ax.set_ylabel("Cases"); ax.set_xlim(0, 100)
                ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", linestyle="--", alpha=.25)
                st.pyplot(fig, use_container_width=True); plt.close(fig)
                st.markdown("</div>", unsafe_allow_html=True)
            with load_right:
                st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>REVIEW CAPACITY</div><h3>Reading workload by case</h3>", unsafe_allow_html=True)
                workload = sorted(((result["filename"], result["pages"]) for result in filtered), key=lambda item: item[1], reverse=True)[:10]
                fig, ax = plt.subplots(figsize=(7, 3.2))
                ax.barh([item[0][:22] for item in workload][::-1], [item[1] for item in workload][::-1], color="#3b9a68")
                ax.set_xlabel("Estimated pages"); ax.spines[["top", "right", "left"]].set_visible(False); ax.grid(axis="x", linestyle="--", alpha=.25)
                st.pyplot(fig, use_container_width=True); plt.close(fig)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>COMPARISON TABLE</div><h3>Case-by-case review</h3>", unsafe_allow_html=True)
            table_rows = [{"Case": result["filename"], "Title": result["title"], "Type": result["case_type"], "Disposition": result["outcome"], "Confidence": f"{result['confidence']}%", "Issues": len(result["issues"]), "Pages": result["pages"]} for result in filtered]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
            st.download_button("Download portfolio CSV", bulk_csv(filtered), "legal-case-portfolio.csv", "text/csv")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='empty-state'><div class='empty-icon'>▦</div><h2>Your portfolio starts here.</h2><p>Select multiple judgments to reveal portfolio-level patterns and prioritize review.</p></div>", unsafe_allow_html=True)
    st.stop()

if view in ("Dashboard", "Analyze case"):
    st.markdown("<div class='hero'><div><div class='eyebrow'>CASE OPERATIONS / 2026</div><h1>See the decision<br><em>before the noise.</em></h1><p>Turn dense judgments into traceable issues, disposition evidence, and a decision-ready brief.</p></div><div class='hero-mark'>⚖<small>01</small></div></div>", unsafe_allow_html=True)
    source, action = st.columns([4, 1], vertical_alignment="bottom")
    with source:
        input_type = st.radio("Input source", ["Upload PDF", "Paste text"], horizontal=True)
        uploaded = st.file_uploader("Drop a judgment PDF here", type="pdf", label_visibility="collapsed") if input_type == "Upload PDF" else None
        pasted = st.text_area("Paste judgment", height=140, placeholder="Paste the judgment or order here...", label_visibility="collapsed") if input_type == "Paste text" else ""
    with action:
        clicked = st.button("Analyze case  →", type="primary", use_container_width=True)

    text = extract_text_from_pdf(uploaded) if uploaded else pasted
    if clicked:
        if not text.strip():
            st.warning("Add a PDF or paste judgment text first.")
        else:
            key = hashlib.sha256(text.encode()).hexdigest()
            with st.spinner(f"Building {mode.lower()} evidence brief..."):
                st.session_state.analysis = analyze_case(text, mode)
                st.session_state.analysis["key"] = key
                st.session_state.source_text = text
            st.success("Analysis ready.")

    data = st.session_state.analysis
    if data:
        st.markdown("<div class='section-heading'><span>CASE SNAPSHOT</span><small>Updated just now</small></div>", unsafe_allow_html=True)
        cards = st.columns(5)
        with cards[0]: metric("Document length", f"{data['words']:,}", f"~{data['pages']} pages")
        with cards[1]: metric("Case type", data["case_type"].replace(" Case", ""), "Classification")
        with cards[2]: metric("Disposition", data["outcome"].split(" /")[0], "Detected language", "gold")
        with cards[3]: metric("Evidence confidence", f"{data['confidence']}%", "Text-grounded", "green")
        with cards[4]: metric("Issues found", len(data["issues"]), "Review points", "blue")

        left, center, right = st.columns([1.1, 1.7, 1.1])
        with left:
            st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>CASE FILE</div><h3>Identity</h3>", unsafe_allow_html=True)
            st.markdown(f"<div class='identity-title'>{data['title']}</div><div class='fact'><span>Court</span><b>{data['court']}</b></div><div class='fact'><span>Judge</span><b>{data['judge']}</b></div><div class='fact'><span>Date</span><b>{data['date']}</b></div></div>", unsafe_allow_html=True)
            st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>DISPOSITION SIGNAL</div><h3>Decision evidence</h3>", unsafe_allow_html=True)
            st.metric("Detected result", data["outcome"])
            st.progress(data["confidence"] / 100)
            st.caption(data["evidence"] or "No explicit dispositive sentence found.")
            st.markdown("</div>", unsafe_allow_html=True)
        with center:
            st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>CASE INTELLIGENCE</div><h3>Evidence confidence</h3>", unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(7, 3))
            bars = ax.barh(["Explicit disposition", "Uncertainty"], [data["confidence"], data["uncertainty"]], color=["#e8ad4e", "#dfe5ea"], height=.5)
            ax.set_xlim(0, 100); ax.set_xlabel("Signal share (%)"); ax.spines[["top", "right", "left"]].set_visible(False); ax.grid(axis="x", linestyle="--", alpha=.25)
            for bar in bars: ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2, f"{bar.get_width():.0f}%", va="center")
            st.pyplot(fig, use_container_width=True); plt.close(fig)
            st.caption("Text evidence confidence is not a prediction of legal merit.")
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown("<div class='dashboard-panel'><div class='panel-kicker'>REVIEW QUEUE</div><h3>Priority issues</h3>", unsafe_allow_html=True)
            for index, issue in enumerate(data["issues"][:4], 1):
                st.markdown(f"<div class='issue-row'><span>{index:02d}</span><p>{issue}</p></div>", unsafe_allow_html=True)
            if not data["issues"]: st.info("No explicit issue statements detected.")
            st.markdown("</div>", unsafe_allow_html=True)

        brief, issues_tab, source_tab = st.tabs(["Decision brief", "Legal issues", "Source text"])
        with brief:
            part1, part2, part3 = split_summary(data["summary"])
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='brief-card'><b>BACKGROUND</b><p>{part1}</p></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='brief-card'><b>ISSUES</b><p>{part2 or 'See the Legal issues tab for extracted questions.'}</p></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='brief-card'><b>JUDGMENT</b><p>{part3 or 'See the disposition evidence above.'}</p></div>", unsafe_allow_html=True)
            st.download_button("Download analysis report", report(data), "lexora-analysis.txt", "text/plain")
        with issues_tab:
            for issue in data["issues"]: st.markdown(f"- {issue}")
        with source_tab:
            st.text_area("Extracted source", st.session_state.source_text, height=320, label_visibility="collapsed")
    else:
        st.markdown("<div class='empty-state'><div class='empty-icon'>✦</div><h2>Your next case starts here.</h2><p>Upload a judgment to populate the dashboard with live evidence, metadata, and review priorities.</p></div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='empty-state'><div class='empty-icon'>⌂</div><h2>Case insights</h2><p>Run an analysis from the dashboard to unlock the case intelligence workspace.</p></div>", unsafe_allow_html=True)
