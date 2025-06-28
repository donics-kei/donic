import streamlit as st
import pandas as pd
import time
import os
import random

# 📱 モバイル最適化スタイル
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px !important;
    line-height: 1.6;
    padding: 0 12px;
}
h1 { font-size: 28px !important; margin-bottom: 1rem; }
div.question-text {
    font-size: 16px !important;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
div[class*="stRadio"] label {
    font-size: 16px !important;
    padding: 6px;
}
</style>
""", unsafe_allow_html=True)

# ロゴ画像の表示（nics_logo.png があれば）
if os.path.exists("nics_logo.png"):
    st.image("nics_logo.png", width=260)

DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(path):
        st.error("問題データファイルが見つかりません。")
        st.stop()
    df = pd.read_csv(path)
    if df.empty:
        st.error("CSVファイルが空です。")
        st.stop()
    return df

# セッション状態初期化
if "page" not in st.session_state:
    st.session_state.page = "start"

# ==== スタートページ ====
if st.session_state.page == "start":
    st.title("SPI試験対策：言語分野（20問）")
    st.markdown("このアプリでは、SPI言語分野の模擬演習を行うことができます。")
    st.markdown("- 各問題には時間制限があります")
    st.markdown("- 回答後すぐに正解・解説が表示されます")
    st.markdown("- 全問終了後にスコアが表示されます")

  if st.button("演習スタート"):
    df = load_questions()
    st.write(f"全問題数：{len(df)}")
    
    filtered = df[df["category"].str.strip() == "言語"]
    st.write(f"言語カテゴリの問題数：{len(filtered)}")
    
    if len(filtered) < 20:
        st.error("言語カテゴリの問題が20問未満です。")
        st.stop()

    random.seed(time.time())
    selected = filtered.sample(n=20, random_state=random.randint(1, 999999)).reset_index(drop=True)
    st.session_state.questions = selected
    ...


        # セッションの questions を明示的にリセット
        st.session_state.pop("questions", None)

        # 完全ランダムな抽出（乱数シードも変動）
        random.seed(time.time())
        selected = filtered.sample(n=20, random_state=random.randint(1, 999999)).reset_index(drop=True)

        st.session_state.questions = selected
        st.session_state.answers = [None] * 20
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * 20
        st.session_state.page = "quiz"
        for k in list(st.session_state.keys()):
            if k.startswith("feedback_") or k.startswith("selection_") or k.startswith("feedback_shown_"):
                del st.session_state[k]
        st.rerun()
# ==== 問題ページ ====
elif st.session_state.page == "quiz":
    questions = st.session_state.get("questions", [])
    q_index = st.session_state.get("q_index", 0)
    num_questions = len(questions)

    if q_index >= num_questions:
        st.session_state.page = "result"
        st.rerun()
        st.stop()

    q = questions.iloc[q_index]
    time_limit = int(q.get("time_limit", DEFAULT_TIME_LIMIT))
    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = max(0, int(time_limit - elapsed))
    feedback_key = f"feedback_shown_{q_index}"

    if remaining == 0 and not st.session_state.get(feedback_key, False):
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.rerun()

    st.header(f"Q{q_index + 1} / {num_questions}")
    st.warning(f"⏳ 残り時間：{remaining} 秒")
    st.markdown(f'<div class="question-text"><b>{q["question"]}</b></div>', unsafe_allow_html=True)

    labels = ["a", "b", "c", "d", "e"]
    choices = [str(q.get(f"choice{i+1}", "")) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    feedback_container = st.empty()

    if not st.session_state.get(feedback_key, False):
        selected = st.radio("選択肢を選んでください：", labeled_choices, index=None, key=f"selection_{q_index}")
        if st.button("回答する") and selected:
            selected_index = labeled_choices.index(selected)
            st.session_state.answers[q_index] = labels[selected_index]
            correct_answer = str(q.get("answer", "")).lower().strip()
            correct = st.session_state.answers[q_index] == correct_answer
            correct_choice = choices[labels.index(correct_answer)] if correct_answer in labels else "不明"
            your_choice = choices[selected_index]

            st.session_state[f"feedback_data_{q_index}"] = {
                "correct": correct,
                "your_choice": your_choice,
                "correct_answer": correct_answer,
                "correct_choice": correct_choice,
                "explanation": q.get("explanation", "")
            }
            st.session_state[feedback_key] = True
            st.rerun()
        else:
            time.sleep(1)
            st.rerun()
    else:
        with feedback_container.container():
            feedback = st.session_state.get(f"feedback_data_{q_index}", {})
            if feedback.get("correct"):
                st.success("正解！")
            else:
                st.error("不正解")
            st.markdown(f"あなたの回答：{st.session_state.answers[q_index].upper()} - {feedback.get('your_choice')}")
            st.markdown(f"正解：{feedback.get('correct_answer').upper()} - {feedback.get('correct_choice')}")
            if feedback.get("explanation"):
                st.info(f"📘 解説：{feedback['explanation']}")

            if st.button("次の問題へ"):
                feedback_container.empty()
                st.session_state.q_index += 1
                st.rerun()
# ==== 結果ページ ====
elif st.session_state.page == "result":
    questions = st.session_state.get("questions", [])
    answers = st.session_state.get("answers", [])
    score = 0
    st.title("📊 採点結果")

    for i, q in questions.iterrows():
        your_answer = answers[i]
        correct_answer = str(q.get("answer", "")).lower().strip()
        labels = ["a", "b", "c", "d", "e"]
        choices = [str(q.get(f"choice{j+1}", "")) for j in range(5)]
        correct_choice = choices[labels.index(correct_answer)] if correct_answer in labels else "不明"
        your_choice = choices[labels.index(your_answer)] if your_answer in labels else "未回答"
        correct_flag = your_answer == correct_answer
        if correct_flag:
            score += 1

        st.markdown(f"**Q{i+1}: {q['question']}** {'✅ 正解' if correct_flag else '❌ 不正解'}")
        st.markdown(f"あなたの回答：{your_answer.upper() if your_answer else '未回答'} - {your_choice}")
        st.markdown(f"正解：{correct_answer.upper()} - {correct_choice}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")

    st.success(f"🎯 最終スコア：{score} / {len(questions)}")

    if st.button("もう一度挑戦する"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

