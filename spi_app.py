import streamlit as st
import pandas as pd
import time
import os

# --- スタイル調整（スマホ対応） ---
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px !important;
    line-height: 1.6;
    padding: 0 12px;
}
h1 { font-size: 22px !important; }
h2 { font-size: 20px !important; }
div.question-text {
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
div[class*="stRadio"] label {
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)

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

# --- セッション初期化 ---
if "page" not in st.session_state:
    st.session_state.page = "select"
    st.session_state.feedback_shown = False

# --- SELECT ページ ---
if st.session_state.page == "select":
    st.markdown("<h1>SPI試験対策</h1>", unsafe_allow_html=True)
    category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    num_q = st.number_input("出題数（最大50問）", 1, 50, 20)
    mode = st.radio("採点方法を選んでください：", ["最後にまとめて採点", "その都度採点"])

    if st.button("開始"):
        df = load_questions()
        filtered = df[df["category"] == category]
        if filtered.empty:
            st.error("このカテゴリーには問題がありません。")
            st.stop()
        selected_q = filtered.sample(min(num_q, len(filtered))).reset_index(drop=True)
        st.session_state.questions = selected_q
        st.session_state.answers = [None] * len(selected_q)
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * len(selected_q)
        st.session_state.mode = mode
        st.session_state.page = "quiz"
        st.session_state.feedback_shown = False
        st.rerun()

# --- QUIZ ページ ---
if st.session_state.page == "quiz":
    questions = st.session_state.questions
    q_index = st.session_state.q_index
    if q_index >= len(questions):
        st.session_state.page = "result"
        st.rerun()

    q = questions.iloc[q_index]
    time_limit = int(q.get("time_limit", DEFAULT_TIME_LIMIT))
    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = max(0, int(time_limit - elapsed))

    if not st.session_state.feedback_shown:
        st.warning(f"⏳ 残り時間：{remaining} 秒")

    if remaining == 0 and not st.session_state.feedback_shown:
        st.error("時間切れ！次の問題へ進みます。")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.session_state.feedback_shown = False
        st.rerun()

    st.markdown(f"<h2>Q{q_index + 1}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='question-text'>{q['question']}</div>", unsafe_allow_html=True)

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q.get(f'choice{i+1}', '')) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    selected = st.radio("選択肢を選んでください：", labeled_choices,
                        index=None, key=f"choice_{q_index}",
                        disabled=st.session_state.feedback_shown)

 feedback_container = st.empty()

    if not st.session_state.feedback_shown:
        if st.button("回答する") and selected:
            selected_index = labeled_choices.index(selected)
            selected_label = labels[selected_index]
            st.session_state.answers[q_index] = selected_label

            if st.session_state.mode == "その都度採点":
                correct_label = str(q.get("answer", "")).lower().strip()
                correct = selected_label == correct_label
                correct_choice = choices[labels.index(correct_label)] if correct_label in labels else "不明"
                your_choice = choices[selected_index]

                with feedback_container.container():
                    if correct:
                        st.success("正解！")
                    else:
                        st.error("不正解")
                    st.markdown(f"あなたの回答：{selected_label.upper()} - {your_choice}")
                    st.markdown(f"正解：{correct_label.upper()} - {correct_choice}")
                    if q.get("explanation"):
                        st.info(f"📘 解説：{q['explanation']}")

                st.session_state.feedback_shown = True

    elif st.session_state.feedback_shown:
        with feedback_container:
            # すでに解説が表示された状態なので、ボタンだけ表示
            if st.button("次の問題へ"):
                feedback_container.empty()
                st.session_state.q_index += 1
                st.session_state.feedback_shown = False
                st.session_state.pop(f"choice_{q_index}", None)
                st.rerun()

    if not st.session_state.feedback_shown:
        time.sleep(1)
        st.rerun()
# --- RESULT ページ ---
if st.session_state.page == "result":
    questions = st.session_state.questions
    answers = st.session_state.answers
    score = 0
    st.subheader("採点結果")

    for i, q in questions.iterrows():
        your_answer = answers[i]
        correct_label = str(q.get("answer", "")).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q.get(f'choice{j+1}', '')) for j in range(5)]
        correct_choice = choices[labels.index(correct_label)] if correct_label in labels else "不明"
        your_choice = choices[labels.index(your_answer)] if your_answer in labels else "未回答"
        correct = your_answer == correct_label
        if correct:
            score += 1

        st.markdown(f"**Q{i+1}: {q['question']}** {'✅ 正解' if correct else '❌ 不正解'}")
        st.markdown(f"あなたの回答：{your_answer.upper() if your_answer else '未回答'} - {your_choice}")
        st.markdown(f"正解：{correct_label.upper()} - {correct_choice}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")

    st.success(f"🎯 最終スコア：{score} / {len(questions)}")
    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
