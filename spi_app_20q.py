import streamlit as st
import pandas as pd
import time
import os

NUM_QUESTIONS = 20
DEFAULT_TIME_LIMIT = 60

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

st.title(f"SPI模擬試験（{st.session_state.category}・{NUM_QUESTIONS}問）")

if q_index < NUM_QUESTIONS:
    q = questions.iloc[q_index]
    if not st.session_state.get("feedback_shown", False):
        st.subheader(f"Q{q_index + 1}: {q['question']}")
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
        labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
        selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{q_index}")
        st.session_state.selected_choice = selected
    else:
        selected = None

    # タイムリミット取得
    try:
        question_time_limit = int(q.get("time_limt", DEFAULT_TIME_LIMIT))
    except:
        question_time_limit = DEFAULT_TIME_LIMIT

    # タイマー開始
    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = int(question_time_limit - elapsed)
    if remaining < 0:
        remaining = 0
    st.warning(f"⏳ 残り時間：{remaining} 秒")

    if remaining == 0:
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.answered.append({
            "question": q['question'],
            "your_answer": None,
            "your_choice": None,
            "correct_answer": str(q['answer']).lower().strip(),
            "correct_choice": q[f"choice{ord(str(q['answer']).lower().strip()) - 96}"],
            "correct": False,
            "explanation": q.get("explanation", "")
        })
        st.session_state.q_index += 1
        st.rerun()

        # 重複定義の削除とインデント修正済み。以下のブロックは不要なので削除します。
