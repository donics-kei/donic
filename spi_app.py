import streamlit as st
import pandas as pd
import random
import time
import os

NUM_QUESTIONS = 40
DEFAULT_TIME_LIMIT = 60  # 予備用（未指定時）

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# 初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if st.session_state.page == "select":
    st.title("SPI模擬試験：1問ずつ・最後に採点・40問版")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        df = load_questions()
        filtered_df = df[df['category'] == st.session_state.category]
        sample_size = min(NUM_QUESTIONS, len(filtered_df))
        st.session_state.questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
        st.session_state.answers = [None] * sample_size
        st.session_state.q_index = 0
        st.session_state.completed = False
        st.session_state.start_times = [None] * sample_size
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

questions = st.session_state.questions
q_index = st.session_state.q_index

st.title(f"SPI模擬試験（{st.session_state.category}・{NUM_QUESTIONS}問）")

if not st.session_state.completed:
    q = questions.iloc[q_index]
    st.subheader(f"Q{q_index + 1}: {q['question']}")

    # 各問題のタイムリミットをCSVの time_limt 列から取得（なければデフォルト）
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
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        if st.session_state.q_index >= NUM_QUESTIONS:
            st.session_state.completed = True
        st.rerun()

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
    selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{q_index}")

    if st.button("次へ"):
        selected_index = labeled_choices.index(selected)
        st.session_state.answers[q_index] = labels[selected_index]
        st.session_state.q_index += 1
        if st.session_state.q_index >= NUM_QUESTIONS:
            st.session_state.completed = True
        st.rerun()

    # 擬似カウントダウン：1秒ごとにリロード
    time.sleep(1)
    st.rerun()

else:
    score = 0
    st.subheader(f"🎯 最終スコア：{score} / {NUM_QUESTIONS}")
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
