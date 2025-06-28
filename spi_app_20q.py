import streamlit as st
import pandas as pd
import time
import os
import random

# 📱 スマホ向けスタイル調整
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px !important;
    line-height: 1.6;
    padding: 0 12px;
    word-wrap: break-word;
}
h1 { font-size: 28px !important; }
h2 { font-size: 20px !important; }
div.question-text {
    font-size: 16px !important;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
div[class*="stRadio"] label {
    font-size: 16px !important;
    line-height: 1.5;
    padding: 8px 4px;
}
section[data-testid="stNotification"], .markdown-text-container {
    font-size: 15px !important;
    line-height: 1.6;
}
button[kind="primary"] {
    font-size: 16px !important;
    padding: 0.6rem 1.2rem;
    margin-top: 1.2rem;
}
</style>
""", unsafe_allow_html=True)

# ロゴ表示（任意）
if os.path.exists("nics_logo.png"):
    st.image("nics_logo.png", width=260)

DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(path):
        st.error("CSVファイルが見つかりません。")
        st.stop()
    df = pd.read_csv(path)
    if df.empty:
        st.error("CSVファイルが空です。")
        st.stop()
    return df

if "page" not in st.session_state:
    st.session_state.page = "start"

# ==== スタート画面 ====
if st.session_state.page == "start":
    st.title("SPI試験対策：言語分野（20問）")
    st.markdown("このアプリでは、SPI言語分野の模擬演習を行うことができます。")
    st.markdown("- 各問題には時間制限があります")
    st.markdown("- 回答後すぐに正解・解説が表示されます")
    st.markdown("- 全問終了後にスコアが表示されます")

    if st.button("演習スタート"):
        df = load_questions()
        filtered = df[df["category"] == "言語"]
        if len(filtered) < 20:
            st.error("「言語」カテゴリの問題が20問未満です。")
            st.stop()

        # 🔁 セッション内の既存questionsを削除して再抽出
        if "questions" in st.session_state:
            del st.session_state["questions"]

        # 🎲 完全ランダム抽出（時刻ベースで毎回異なるシード）
        random.seed(time.time())
        selected = filtered.sample(n=20, random_state=random.randint(1, 1_000_000)).reset_index(drop=True)

        st.session_state.questions = selected
        st.session_state.answers = [None] * 20
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * 20
        st.session_state.page = "quiz"
        for k in list(st.session_state.keys()):
            if k.startswith("feedback_") or k.startswith("selection_") or k.startswith("feedback_shown_"):
                del st.session_state[k]
        st.rerun()

