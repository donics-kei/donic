import streamlit as st
import pandas as pd
import time
import os

NUM_QUESTIONS = 20
DEFAULT_TIME_LIMIT = None

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

if "page" not in st.session_state:
    st.session_state.page = "select"

if st.session_state.page == "select":
    st.title("SPI演習：最後にまとめて採点・出題数選択版")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    st.session_state.temp_num_questions = st.number_input("出題数を選んでください：", min_value=1, max_value=100, value=20, step=1)
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.num_questions = st.session_state.temp_num_questions
        df = load_questions()
        filtered_df = df[df['category'] == st.session_state.category]
        sample_size = min(st.session_state.num_questions, len(filtered_df))
        st.session_state.questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
        st.session_state.q_index = 0
        st.session_state.answers = [None] * sample_size
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

questions = st.session_state.questions
answers = st.session_state.answers
num_questions = len(questions)

st.title(f"SPI模擬試験（{st.session_state.category}・{num_questions}問）")
st.write("---")

for i in range(num_questions):
    q = questions.iloc[i]
    st.subheader(f"Q{i+1}: {q['question']}")
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    if answers[i] in labels:
        selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{i}", index=labels.index(answers[i]))
    else:
        selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{i}")

    if selected:
        st.session_state.answers[i] = selected.split('.')[0]

if st.button("採点する"):
    results = []
    score = 0
    for i in range(num_questions):
        q = questions.iloc[i]
        your_answer = st.session_state.answers[i]
        correct_answer = str(q['answer']).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
        correct_index = labels.index(correct_answer)
        your_choice = choices[labels.index(your_answer)] if your_answer in labels else None
        correct_choice = choices[correct_index]
        correct = your_answer == correct_answer
        if correct:
            score += 1

        results.append({
            "question": q['question'],
            "your_answer": your_answer,
            "your_choice": your_choice,
            "correct_answer": correct_answer,
            "correct_choice": correct_choice,
            "correct": correct,
            "explanation": q.get("explanation", "")
        })

    st.success(f"あなたのスコアは {score} / {num_questions} 点です")
    st.write("---")
    st.subheader("詳細結果")
    df_result = pd.DataFrame(results)
    df_result.index = [f"Q{i+1}" for i in range(len(df_result))]
    st.dataframe(df_result)

    if st.button("もう一度解く"):
        del st.session_state.page
        st.rerun()
