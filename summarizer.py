import os
import re
from collections import Counter

import streamlit as st


def split_summary(summary_text):
    sentences = re.split(r"(?<=[.!?])\s+", summary_text.strip())

    part1 = " ".join(sentences[:4]) if len(sentences) > 4 else summary_text
    part2 = " ".join(sentences[4:8]) if len(sentences) > 8 else ""
    part3 = " ".join(sentences[8:]) if len(sentences) > 8 else ""

    return part1.strip(), part2.strip(), part3.strip()

@st.cache_resource
def load_model(model_name):
    try:
        from transformers import pipeline

        return pipeline("summarization", model=model_name)
    except Exception:
        return None

summarizer = None

def chunk_text(text, max_chars=2200):
    sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " ").strip())
    chunks, current = [], ""

    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 <= max_chars:
            current += (" " if current else "") + sentence
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def _extractive_summary(text, limit=12):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 40]
    if not sentences:
        return text[:3000].strip()
    frequent = Counter(re.findall(r"[a-zA-Z]{4,}", text.lower()))
    markers = ("held", "ordered", "accordingly", "issue", "appellant", "respondent", "court")
    scored = []
    for index, sentence in enumerate(sentences):
        words = re.findall(r"[a-zA-Z]{4,}", sentence.lower())
        score = sum(frequent[word] for word in words) / max(len(words), 1)
        score += sum(2 for marker in markers if marker in sentence.lower())
        scored.append((score, index, sentence))
    selected = sorted(scored, reverse=True)[:limit]
    return " ".join(sentence for _, _, sentence in sorted(selected, key=lambda item: item[1]))

def summarize_legal_text(text, mode="Fast"):
    text = re.sub(r"\s+", " ", text).strip()

    if mode == "Fast":
        return _extractive_summary(text, limit=10)

    model_name = os.getenv(
        "LEGAL_SUMMARIZATION_MODEL",
        "sshleifer/distilbart-cnn-12-6" if mode == "Balanced" else "facebook/bart-large-cnn",
    )
    summarizer = load_model(model_name)
    chunks = chunk_text(text)

    if not summarizer:
        return _extractive_summary(text)

    summaries = []
    for chunk in chunks:
        summary = summarizer(
            chunk,
            max_length=180,
            min_length=45,
            do_sample=False
        )
        summaries.append(summary[0]["summary_text"])

    return " ".join(summaries)

def predict_case_outcome(text):
    lowered = re.sub(r"\s+", " ", text.lower())
    patterns = {
        "Allowed / successful": r"\b(appeal|petition|application)\s+(is|was)\s+(allowed|accepted|granted)|relief\s+(is|was)\s+granted",
        "Dismissed / unsuccessful": r"\b(appeal|petition|application)\s+(is|was)\s+dismissed|relief\s+(is|was)\s+denied",
        "Partly allowed": r"partly\s+(allowed|granted)|allowed\s+in\s+part",
        "Conviction upheld": r"conviction\s+(is|was)\s+(upheld|confirmed)",
        "Conviction set aside": r"conviction\s+(is|was)\s+(set aside|quashed)",
    }
    label, count = max(((label, len(re.findall(pattern, lowered))) for label, pattern in patterns.items()), key=lambda item: item[1])
    if not count:
        return "Inconclusive", 50.0, 50.0, "No explicit dispositive language was detected."
    evidence = re.search(r"[^.]{0,100}(allowed|dismissed|granted|denied|upheld|quashed|set aside)[^.]{0,160}", lowered)
    confidence = min(95.0, 60.0 + count * 10.0)
    return label, confidence, round(100 - confidence, 2), evidence.group(0).strip() if evidence else ""

def extract_case_title(text):
    lines = text.split("\n")
    for line in lines[:15]:
        if re.search(r"\b(vs?\.?|versus)\b", line, re.IGNORECASE):
            return line.strip()
    return "Not detected"

def detect_case_type(text):
    text = text.lower()

    if any(k in text for k in ["ipc", "crpc", "fir", "offence", "accused", "conviction"]):
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


def extract_legal_issues(text, limit=5):
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
    markers = ("whether", "issue", "question", "challenge", "validity", "liable", "jurisdiction")
    return [sentence.strip() for sentence in sentences if any(marker in sentence.lower() for marker in markers)][:limit]

