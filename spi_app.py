import streamlit as st
import pandas as pd
import time
import random

# --------------------------
# 質問データ読み込み（Excel）
# --------------------------
@st.cache_data
def load_questions():
    df = pd.read_excel("spi_questions.xlsx")
    return df

questions_all = load_questions()

# --------------------------
# セッション状態の初期化
# --------------------------
if "page" not in st.session_state:
    st.session_state.page = "select"
if "questions" not in st.session_state:
    st.session_state.questions = []
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answered" not in st.session_state:
    st.session_state.answered = []
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = time.time()

# --------------------------
# ページ1：カテゴリ選択
# --------------------------
if st.session_state.page == "select":
    st.title("SPI 模擬試験")
    category = st.radio("カテゴリを選んでください", ["すべて", "言語", "非言語"])
    if st.button("スタート"):
        if category == "すべて":
            filtered = questions_all
        else:
            filtered = questions_all[questions_all["category"] == category]

        if len(filtered) < 40:
            st.error("40問以上の問題が必要です。")
        else:
            st.session_state.questions = filtered.sample(40).reset_index(drop=True)
            st.session_state.page = "quiz"
            st.session_state.q_index = 0
            st.session_state.score = 0
            st.session_state.answered = []
            st.session_state.question_start_time = time.time()
            st.rerun()

# --------------------------
# ページ2：出題＆解答処理
# --------------------------
elif st.session_state.page == "quiz":
    if st.session_state.q_index >= len(st.session_state.questions):
        st.session_state.page = "result"
        st.rerun()

    q = st.session_state.questions.iloc[st.session_state.q_index]
    st.subheader(f"Q{st.session_state.q_index + 1}: {q['question']}")
    st.caption(f"カテゴリ：{q['category']}")

    choices = [q['choice1'], q['choice2'], q['choice3'], q['choice4']]
    answer_time_limit = int(q['time_limit'])

    remaining = answer_time_limit - int(time.time() - st.session_state.question_start_time)
    st.markdown(f"### ⏳ 残り時間：{max(0, remaining)} 秒")
    st.progress(max(0, remaining) / answer_time_limit)

    selected = st.radio("選択肢を選んでください：", choices, key=f"q{st.session_state.q_index}")

    if st.button("解答する") or remaining <= 0:
        correct_idx = int(q['answer']) - 1
        selected_idx = choices.index(selected) if selected in choices else -1
        is_correct = (selected_idx == correct_idx)

        st.session_state.answered.append({
            "question": q['question'],
            "your_answer": choices[selected_idx] if selected_idx >= 0 else "無回答",
            "correct_answer": choices[correct_idx],
            "is_correct": is_correct if selected_idx >= 0 else False,
            "explanation": q['explanation'],
            "category": q['category'],
            "time_limit": q['time_limit'],
            "time_used": min(answer_time_limit, int(time.time() - st.session_state.question_start_time))
        })

        if is_correct:
            st.session_state.score += 1

        st.session_state.q_index += 1
        st.session_state.question_start_time = time.time()
        st.rerun()

# --------------------------
# ページ3：結果表示と解説
# --------------------------
elif st.session_state.page == "result":
    st.title("✅ 結果発表")
    total = len(st.session_state.answered)
    correct = st.session_state.score
    wrong = total - correct

    st.write(f"得点：{correct} / {total}")
    st.write(f"正解数：{correct}問　|　不正解数：{wrong}問")
    st.markdown("---")
    st.subheader("📘 解説一覧")

    for i, a in enumerate(st.session_state.answered):
        st.markdown(f"**Q{i+1}: {a['question']}**")
        st.write(f"- あなたの回答：{a['your_answer']}")
        st.write(f"- 正解：{a['correct_answer']}")
        st.write(f"- 結果：{'✅ 正解' if a['is_correct'] else '❌ 不正解'}")
        st.write(f"- 制限時間：{a['time_limit']}秒　使用時間：{a['time_used']}秒")
        st.write(f"- カテゴリ：{a['category']}")
        st.info(a['explanation'])
