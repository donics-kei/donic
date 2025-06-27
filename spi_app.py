import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(page_title="SPI練習アプリ", layout="centered")

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

if "page" not in st.session_state:
    st.session_state.page = "select"
    st.session_state.feedback_shown = False

if st.session_state.page == "select":
    st.title("SPI練習アプリ")
    category = st.radio("出題カテゴリーを選択", ["言語", "非言語"])
    num_q = st.slider("出題数", 1, 50, 10)
    mode = st.radio("採点モード", ["その都度採点", "最後にまとめて採点"])
    if st.button("スタート！"):
        df = load_questions()
        filtered = df[df["category"] == category]
        if filtered.empty:
            st.error("そのカテゴリーには問題がありません。")
            st.stop()
        selected = filtered.sample(min(num_q, len(filtered))).reset_index(drop=True)
        st.session_state.questions = selected
        st.session_state.q_index = 0
        st.session_state.answers = [None] * len(selected)
        st.session_state.start_times = [None] * len(selected)
        st.session_state.mode = mode
        st.session_state.page = "quiz"
        st.session_state.feedback_shown = False
        st.rerun()

if st.session_state.page == "quiz":
    if st.session_state.q_index >= len(st.session_state.questions):
        st.session_state.page = "result"
        st.rerun()

    q_index = st.session_state.q_index
    q = st.session_state.questions.iloc[q_index]
    time_limit = int(q.get("time_limit", DEFAULT_TIME_LIMIT))
    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()
    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = max(0, int(time_limit - elapsed))

    if not st.session_state.feedback_shown:
        st.info(f"⏳ 残り時間：{remaining} 秒")

    if remaining == 0 and not st.session_state.feedback_shown:
        st.error("時間切れ！次の問題へ進みます")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.session_state.feedback_shown = False
        st.rerun()

    st.header(f"Q{q_index + 1}")
    st.markdown(f"<div class='question-text'>{q['question']}</div>", unsafe_allow_html=True)

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q.get(f"choice{i+1}", '')) for i in range(5)]
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
            st.session_state.feedback_shown = True

            # --- 採点と解説表示 ---
            if st.session_state.mode == "その都度採点":
                correct_label = str(q.get("answer", "")).lower().strip()
                correct = selected_label == correct_label
                correct_choice = choices[labels.index(correct_label)] if correct_label in labels else "不明"
                your_choice = choices[selected_index]

                with feedback_container.container():
                    st.markdown(f"あなたの回答：{selected_label.upper()} - {your_choice}")
                    st.markdown(f"正解：{correct_label.upper()} - {correct_choice}")
                    if correct:
                        st.success("正解！")
                    else:
                        st.error("不正解")
                    if q.get("explanation"):
                        st.info(f"📘 解説：{q['explanation']}")

                    # --- 次の問題へボタン（解説の直後） ---
                    if st.button("次の問題へ"):
                        feedback_container.empty()
                        st.session_state.q_index += 1
                        st.session_state.feedback_shown = False
                        st.session_state.pop(f"choice_{q_index}", None)
                        st.rerun()

            st.stop()

elif st.session_state.feedback_shown:
        # --- 再描画時にも次の問題へボタンを確実に表示 ---
        with feedback_container.container():
            selected_label = st.session_state.answers[q_index]
            correct_label = str(q.get("answer", "")).lower().strip()
            correct = selected_label == correct_label
            correct_choice = choices[labels.index(correct_label)] if correct_label in labels else "不明"
            your_choice = choices[labels.index(selected_label)] if selected_label in labels else "未回答"

            st.markdown(f"あなたの回答：{selected_label.upper()} - {your_choice}")
            st.markdown(f"正解：{correct_label.upper()} - {correct_choice}")
            if correct:
                st.success("正解！")
            else:
                st.error("不正解")
            if q.get("explanation"):
                st.info(f"📘 解説：{q['explanation']}")

            if st.button("次の問題へ"):
                feedback_container.empty()
                st.session_state.q_index += 1
                st.session_state.feedback_shown = False
                st.session_state.pop(f"choice_{q_index}", None)
                st.rerun()

    if not st.session_state.feedback_shown:
        time.sleep(1)
        st.rerun()
# --- 結果ページ ---
if st.session_state.page == "result":
    st.subheader("🎓 採点結果")
    score = 0
    questions = st.session_state.questions
    answers = st.session_state.answers

    for i, q in questions.iterrows():
        your = answers[i]
        correct = str(q.get("answer", "")).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q.get(f"choice{j+1}", '')) for j in range(5)]
        correct_choice = choices[labels.index(correct)] if correct in labels else "不明"
        your_choice = choices[labels.index(your)] if your in labels else "未回答"
        is_correct = your == correct
        if is_correct:
            score += 1

        st.markdown(f"**Q{i+1}: {q['question']}** {'✅' if is_correct else '❌'}")
        st.markdown(f"あなたの回答：{your.upper() if your else '未回答'} - {your_choice}")
        st.markdown(f"正解：{correct.upper()} - {correct_choice}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")

    st.success(f"🎯 最終スコア：{score} / {len(questions)}")

    if st.button("もう一度挑戦する"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

