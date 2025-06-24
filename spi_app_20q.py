import streamlit as st
import pandas as pd
import time
import os

NUM_QUESTIONS = 20
DEFAULT_TIME_LIMIT = None  # 使用しないが念のため保持

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# 初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if st.session_state.page == "select":
    st.title("SPI模擬試験：1問ずつ採点・20問版")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        df = load_questions()
        filtered_df = df[df['category'] == st.session_state.category]
        sample_size = min(NUM_QUESTIONS, len(filtered_df))
        st.session_state.questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.answered = []
        st.session_state.start_times = [None] * sample_size
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

questions = st.session_state.questions
q_index = st.session_state.q_index

# 各問題の制限時間をリストで取り出す（J列: time_limit）
time_limit_col = 'time_limit' if 'time_limit' in questions.columns else 'time_limt'
time_limits = questions[time_limit_col].fillna(60).astype(int).tolist()

st.title(f"SPI模擬試験（{st.session_state.category}・{NUM_QUESTIONS}問）")

if q_index < NUM_QUESTIONS:
    q = questions.iloc[q_index]
    question_time_limit = time_limits[q_index]
    # 問題・解説処理（既存コード省略）
    ...
else:
    st.success("✅ すべての問題が終了しました！")
    st.metric("あなたの最終スコア", f"{st.session_state.score} / {NUM_QUESTIONS}")
    st.markdown("---")
    st.subheader("詳細結果：")
    df_result = pd.DataFrame(st.session_state.answered)
    df_result.index = [f"Q{i+1}" for i in range(len(df_result))]
    st.dataframe(df_result)

    # リトライオプション
    if st.button("もう一度解く"):
        del st.session_state.page
        st.rerun()

        if st.session_state.get("feedback_shown", False) and st.session_state.get("selected_choice"):
            if st.button("次の問題へ"):
                st.session_state.q_index += 1
                st.session_state.feedback_shown = False
                st.session_state.selected_choice = None
                st.rerun()
