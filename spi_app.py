import streamlit as st
import pandas as pd
import random
import time
import os

# CSVファイルを読み込む関数（キャッシュ付き）
@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# 初期画面または未選択状態の確認
if "page" not in st.session_state:
    st.session_state.page = "select"

if st.session_state.page == "select":
    st.title("SPI試験対策へようこそ")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

# カテゴリー選択済みで初期化されていなければセットアップ
if "questions" not in st.session_state:
    df = load_questions()
    filtered_df = df[df['category'] == st.session_state.category]
    if len(filtered_df) < 40:
        st.warning(f"注意：『{st.session_state.category}』カテゴリの問題数が40問未満です（{len(filtered_df)}問）。")
    sample_size = min(40, len(filtered_df))
    filtered = filtered_df.sample(n=sample_size).reset_index(drop=True)
    st.session_state.questions = filtered
    st.session_state.score = 0
    st.session_state.q_index = 0
    st.session_state.answered = []
    st.session_state.start_times = []

questions = st.session_state.questions

st.title(f"SPI試験対策（{st.session_state.category}）")

# 問題表示と回答処理
if st.session_state.q_index < len(questions):
    q = questions.iloc[st.session_state.q_index]
    st.subheader(f"Q{st.session_state.q_index + 1}: {str(q['question']).strip()}")

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q['choice1']).strip(), str(q['choice2']).strip(), str(q['choice3']).strip(), str(q['choice4']).strip(), str(q['choice5']).strip()]
    labeled_choices = [f"{label}. {choice}" for label, choice in zip(labels, choices)]

    if len(st.session_state.start_times) <= st.session_state.q_index:
        st.session_state.start_times.append(time.time())

    elapsed = time.time() - st.session_state.start_times[st.session_state.q_index]
    time_limit = int(q['time_limit']) if 'time_limit' in q and not pd.isna(q['time_limit']) else 60  # デフォルト60秒
    remaining = int(time_limit - elapsed)
    st.write(f"残り時間：⏱️ {remaining} 秒")

    if remaining <= 0:
        st.warning("時間切れ（この問題は無回答として処理されます）")
        st.session_state.answered.append({
            "question": str(q['question']).strip(),
            "correct": False,
            "your_answer": None,
            "your_choice": None,
            "correct_answer": str(q['answer']).lower().strip(),
            "correct_choice": choices[labels.index(str(q['answer']).lower().strip())],
            "explanation": q.get("explanation", "")
        })
        st.session_state.q_index += 1
        st.rerun()

    selected = st.radio("選択肢を選んでください（a〜e）:", labeled_choices, key=f"q{st.session_state.q_index}")

    if st.button("次へ"):
        correct_index = labels.index(str(q['answer']).lower().strip())
        selected_index = labeled_choices.index(selected)
        is_correct = selected_index == correct_index
        your_answer = labels[selected_index]
        your_choice = choices[selected_index]

        if is_correct:
            st.session_state.score += 1

        st.session_state.answered.append({
            "question": str(q['question']).strip(),
            "correct": is_correct,
            "your_answer": your_answer,
            "your_choice": your_choice,
            "correct_answer": str(q['answer']).lower().strip(),
            "correct_choice": choices[correct_index],
            "explanation": q.get("explanation", "")
        })
        st.session_state.q_index += 1
        st.rerun()

else:
    st.success("全問終了！")
    st.write(f"あなたの得点：{st.session_state.score} / {len(st.session_state.answered)}")

    st.subheader("解説")
    for idx, result in enumerate(st.session_state.answered):
        st.markdown(f"**Q{idx+1}: {result['question']}**")
        st.markdown("✅ 正解" if result['correct'] else "❌ 不正解")
        st.markdown(f"あなたの回答：{result['your_answer'].upper() if result['your_answer'] else '未回答'} - {result['your_choice'] if result['your_choice'] else '―'}")
        st.markdown(f"正解：{result['correct_answer'].upper()} - {result['correct_choice']}")
        if result['explanation']:
            st.markdown(f"📘 解説：{result['explanation']}")
        st.markdown("---")
