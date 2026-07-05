import streamlit as st
import hashlib
import sqlite3
import requests
from datetime import datetime

st.set_page_config(page_title="المصنع الشامل", layout="wide", page_icon="🏭")

DB_PATH = "translation_memory.db"
API_URL = "https://libretranslate.de/translate"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS translations (
        source_hash TEXT PRIMARY KEY,
        source_text TEXT,
        target_text TEXT,
        source_lang TEXT,
        target_lang TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

def get_tm(text, src, tgt):
    if not text.strip():
        return None
    h = hashlib.md5(f"{src}:{tgt}:{text}".encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute(
            "SELECT target_text FROM translations WHERE source_hash=?",
            (h,)
        ).fetchone()
        conn.close()
        return res[0] if res else None
    except:
        return None

def save_tm(text, trans, src, tgt):
    if not text or not trans:
        return
    h = hashlib.md5(f"{src}:{tgt}:{text}".encode()).hexdigest()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO translations VALUES (?,?,?,?,?,?)",
            (h, text, trans, src, tgt, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except:
        pass

def translate(text, src="en", tgt="ar"):
    if not text.strip():
        return ""

    cached = get_tm(text, src, tgt)
    if cached:
        return cached

    try:
        r = requests.post(
            API_URL,
            data={
                "q": text[:4000],
                "source": src,
                "target": tgt,
                "format": "text"
            },
            timeout=20
        )
        if r.status_code == 200:
            result = r.json().get("translatedText", text)
            save_tm(text, result, src, tgt)
            return result
    except:
        pass

    return text

def main():
    init_db()

    st.title("🏭 المصنع الشامل للترجمة")
    st.caption("نسخة سحابية - Streamlit Cloud")

    col1, col2 = st.columns(2)

    with col1:
        src = st.selectbox("من", ["en", "ar", "fr", "de", "es"], index=0)

    with col2:
        tgt = st.selectbox("إلى", ["ar", "en", "fr", "de", "es"], index=0)

    uploaded_file = st.file_uploader("ارفع ملف TXT", type=["txt"])

    if uploaded_file:
        st.info(f"تم رفع الملف: {uploaded_file.name}")

    if uploaded_file and st.button("🚀 ترجم", type="primary", use_container_width=True):
        with st.spinner("جاري الترجمة..."):
            text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            result = translate(text, src, tgt)

            st.success("✅ تمت الترجمة")
            st.text_area("النتيجة:", result, height=350)

            st.download_button(
                "📥 تحميل الترجمة",
                result,
                file_name="translated.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
