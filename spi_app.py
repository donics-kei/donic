import streamlit as st
import pandas as pd
import random
import time
import os

NUM_QUESTIONS = 40
DEFAULT_TIME_LIMIT = 60  # 秒数（1問あたり）

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# 初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if st.session_state.page == "select":
    st.title("SPI模擬試験：一括採点・40問版")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

# 質問読み込みと初期化
if "questions" not in st.session_state:
    df = load_questions()
    filtered_df = df[df['category'] == st.session_state.category]
    if len(filtered_df) < NUM_QUESTIONS:
        st.warning(f"注意：『{st.session_state.category}』カテゴリの問題数が{NUM_QUESTIONS}問未満です（{len(filtered_df)}問）。")
    sample_size = min(NUM_QUESTIONS, len(filtered_df))
    questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
    st.session_state.questions = questions
    st.session_state.answers = [None] * sample_size
    st.session_state.start_times = [time.time()] * sample_size
    st.session_state.completed = False

questions = st.session_state.questions

st.title(f"SPI模擬試験（{st.session_state.category}・{NUM_QUESTIONS}問）")

if not st.session_state.completed:
    for i, q in questions.iterrows():
        st.subheader(f"Q{i + 1}: {q['question']}")
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
        labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
        selected = st.radio("選択肢を選んでください：", labeled_choices, index=-1, key=f"q{i}")
        if selected:
            selected_index = labeled_choices.index(selected)
            st.session_state.answers[i] = labels[selected_index]

    if st.button("採点する"):
        st.session_state.completed = True
        st.rerun()
else:
    score = 0
    st.success("全40問終了！ 以下が採点結果です：")
    st.subheader("採点結果と解説")
    for i, q in questions.iterrows():
        your_answer = st.session_state.answers[i]
        correct_answer = str(q['answer']).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
        correct_index = labels.index(correct_answer)
        correct_choice = choices[correct_index]

        if your_answer == correct_answer:
            st.markdown(f"**Q{i+1}: {q['question']}** ✅ 正解")
            score += 1
        else:
            st.markdown(f"**Q{i+1}: {q['question']}** ❌ 不正解")

        if your_answer:
            your_choice = choices[labels.index(your_answer)]
            st.markdown(f"あなたの回答：{your_answer.upper()} - {your_choice}")
        else:
            st.markdown("あなたの回答：未回答")

        st.markdown(f"正解：{correct_answer.upper()} - {correct_choice}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")

    st.subheader(f"最終スコア：{score} / {NUM_QUESTIONS}")
