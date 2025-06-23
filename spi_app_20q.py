import streamlit as st
import pandas as pd
import random
import time
import os

# 出題数を20問に制限
NUM_QUESTIONS = 20

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions.csv")
    return pd.read_csv(csv_path)

# 初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if st.session_state.page == "select":
    st.title("SPI模擬試験：1問ずつ採点・20問版")
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
    st.session_state.q_index = 0
    st.session_state.score = 0
    st.session_state.answered = []

questions = st.session_state.questions

st.title(f"SPI模擬試験（{st.session_state.category}・{NUM_QUESTIONS}問）")

if st.session_state.q_index < NUM_QUESTIONS:
    q = questions.iloc[st.session_state.q_index]
    st.subheader(f"Q{st.session_state.q_index + 1}: {q['question']}")

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{st.session_state.q_index}")
    if st.button("回答する"):
        selected_index = labeled_choices.index(selected)
        your_answer = labels[selected_index]
        correct_answer = str(q['answer']).lower().strip()
        correct_index = labels.index(correct_answer)
        is_correct = your_answer == correct_answer
        your_choice = choices[selected_index]
        correct_choice = choices[correct_index]

        if is_correct:
            st.success("正解！")
            st.session_state.score += 1
        else:
            st.error("不正解")

        st.markdown(f"**あなたの回答：{your_answer.upper()} - {your_choice}**")
        st.markdown(f"**正解：{correct_answer.upper()} - {correct_choice}**")
        if q.get("explanation"):
            st.info(f"📘 解説：{q['explanation']}")

        st.session_state.answered.append({
            "question": q['question'],
            "your_answer": your_answer,
            "your_choice": your_choice,
            "correct_answer": correct_answer,
            "correct_choice": correct_choice,
            "correct": is_correct,
            "explanation": q.get("explanation", "")
        })

        st.session_state.q_index += 1
        st.rerun()
else:
    st.success("全20問終了！")
    st.write(f"あなたの得点：{st.session_state.score} / {NUM_QUESTIONS}")

    st.subheader("解説まとめ")
    for idx, result in enumerate(st.session_state.answered):
        st.markdown(f"**Q{idx+1}: {result['question']}**")
        st.markdown("✅ 正解" if result['correct'] else "❌ 不正解")
        st.markdown(f"あなたの回答：{result['your_answer'].upper()} - {result['your_choice']}")
        st.markdown(f"正解：{result['correct_answer'].upper()} - {result['correct_choice']}")
        if result['explanation']:
            st.markdown(f"📘 解説：{result['explanation']}")
        st.markdown("---")
