import streamlit as st
from transformers import pipeline


def split_summary(summary_text):
    sentences = summary_text.split(". ")

    part1 = ". ".join(sentences[:4]) + "." if len(sentences) > 4 else summary_text
    part2 = ". ".join(sentences[4:8]) + "." if len(sentences) > 8 else ""
    part3 = ". ".join(sentences[8:]) if len(sentences) > 8 else ""

    return part1.strip(), part2.strip(), part3.strip()

@st.cache_resource
def load_models():
    summarizer = pipeline("summarization", model="t5-small")
    sentiment = pipeline("sentiment-analysis")
    return summarizer, sentiment

summarizer, sentiment_analyzer = load_models()

def chunk_text(text, max_chars=600):
    sentences = text.split(". ")
    chunks, current = [], ""

    for sentence in sentences:
        if len(current) + len(sentence) < max_chars:
            current += sentence + ". "
        else:
            chunks.append(current)
            current = sentence + ". "

    if current:
        chunks.append(current)

    return chunks[:4]  # speed cap

def summarize_legal_text(text):
    text = text.replace("\n", " ").strip()
    chunks = chunk_text(text)

    summaries = []
    for chunk in chunks:
        summary = summarizer(
            chunk,
            max_length=200,
            min_length=100,
            do_sample=False
        )
        summaries.append(summary[0]["summary_text"])

    return " ".join(summaries)

def predict_case_outcome(text):
    result = sentiment_analyzer(text[:800])[0]
    if result["label"] == "POSITIVE":
        win = round(result["score"] * 100, 2)
    else:
        win = round((1 - result["score"]) * 100, 2)
    return win, 100 - win

def extract_case_title(text):
    lines = text.split("\n")
    for line in lines[:15]:
        if " vs " in line.lower() or " v. " in line.lower():
            return line.strip()
    return "Not detected"

def detect_case_type(text):
    text = text.lower()

    if any(k in text for k in ["ipc", "crpc", "fir", "offence", "accused"]):
        return "Criminal Case"
    elif any(k in text for k in ["contract", "agreement", "damages", "civil"]):
        return "Civil Case"
    elif any(k in text for k in ["constitution", "article", "writ"]):
        return "Constitutional Case"
    elif any(k in text for k in ["gst", "tax", "income tax"]):
        return "Tax Case"
    elif any(k in text for k in ["service", "employment", "promotion"]):
        return "Service / Employment Case"
    else:
        return "General Legal Case"

