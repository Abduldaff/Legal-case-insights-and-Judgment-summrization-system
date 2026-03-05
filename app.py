

import streamlit as st
from pdf_utils import extract_text_from_pdf
from summarizer import (
    summarize_legal_text,
    predict_case_outcome,
    extract_case_title,
    detect_case_type,
    split_summary
)

#from pdf_generator import generate_pdf
import matplotlib.pyplot as plt




def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()



st.title("⚖️ AI-Powered Legal Case Judgment Analyzer")

# Input selection
choice = st.radio("Choose input type:", ["Upload PDF", "Paste Text"])
text = ""

if choice == "Upload PDF":
    file = st.file_uploader("Upload Legal Judgment PDF", type="pdf")
    if file:
        text = extract_text_from_pdf(file)
else:
    text = st.text_area("Paste Legal Judgment Text", height=300)

# Action button
if st.button("Analyze Case"):
    if text.strip():
        with st.spinner("Analyzing legal document..."):
            # Summary
            summary = summarize_legal_text(text)

            # Case metadata
            case_title = extract_case_title(text)
            case_type = detect_case_type(text)

            # Prediction
            win_prob, loss_prob = predict_case_outcome(text)

            

        # Display results
        #st.markdown('<div class="📄 Case Details">', unsafe_allow_html=True)
        st.subheader("📄 Case Details")
        st.markdown(f"**Case Title:** {case_title}")
        st.markdown(f"**Case Type:** {case_type}")
        st.markdown('</div>', unsafe_allow_html=True)

       # st.markdown('<div class="card">', unsafe_allow_html=True)
        

        st.subheader("📌 Case Summary")

        part1, part2, part3 = split_summary(summary)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>🧐Case Background</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel-body'>", unsafe_allow_html=True)
        st.write(part1)
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>⚖️ Legal Issues</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel-body'>", unsafe_allow_html=True)
        st.write(part2 if part2 else "Not explicitly mentioned.")
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-header'>📜 Judgment / Decision</div>", unsafe_allow_html=True)
        st.markdown("<div class='panel-body'>", unsafe_allow_html=True)
        st.write(part3 if part3 else "Decision details summarized above.")
        st.markdown("</div></div>", unsafe_allow_html=True)


        st.subheader("📊 Case Outcome Prediction")

        win_prob, loss_prob = predict_case_outcome(text)

        col1, col2 = st.columns(2)

# 🔹 LEFT PANEL — Prediction Values
        with col1:
            st.markdown("""
                    <div class="panel">
                    <div class="panel-header">🔢 Prediction Values</div>
                    <div class="panel-body">
            """, unsafe_allow_html=True)

            st.write(f"✅ **Winning Probability:** {win_prob}%")
            st.progress(win_prob / 100)
            st.write(f"❌ **Losing Probability:** {loss_prob}%")

            st.markdown("</div></div>", unsafe_allow_html=True)

# 🔹 RIGHT PANEL — Pie Chart
        with col2:
            st.markdown("""
                    <div class="panel">
                    <div class="panel-header">🧮 Prediction Chart</div>
                    <div class="panel-body">
                """, unsafe_allow_html=True)

            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()
            ax.pie(
                [win_prob, loss_prob],
                labels=["Winning", "Losing"],
                autopct="%1.1f%%",
                startangle=90
            )
            ax.axis("equal")

            st.pyplot(fig)

            st.markdown("</div></div>", unsafe_allow_html=True)

        # PDF Download
        #pdf_bytes = generate_pdf(case_title, case_type, summary, win_prob, loss_prob)
        #st.download_button(
         #   label="📥 Download Analysis Report (PDF)",
          #  data=pdf_bytes,
           # file_name="legal_case_analysis.pdf",
            #mime="application/pdf"
        #)

    else:
        st.warning("Please upload a PDF or paste text.")
