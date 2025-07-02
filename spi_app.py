import streamlit as st
import pandas as pd
import time
import os

DEFAULT_TIME_LIMIT = 60  # 秒

@st.cache_data
def load_questions():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# ===== 初期化 =====
defaults = {
    "page": "select",
    "q_index": 0,
    "stage": "quiz",
    "answers": [],
    "start_times": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===== 質問復旧対応 =====
if st.session_state.page != "select" and "questions" not in st.session_state:
    try:
        df = load_questions()
        fallback_cat = st.session_state.get("category", "言語")
        fallback_num = st.session_state.get("num_questions", 20)
        filtered = df[df["category"] == fallback_cat]
        st.session_state.questions = filtered.sample(n=fallback_num).reset_index(drop=True)
        st.warning("⚠️ セッションが切れたため、問題を復元しました。")
    except:
        st.session_state.page = "select"
        st.rerun()

# ===== 表示関数 =====
def draw_quiz(q, idx, choices, labeled_choices, labels):
    radio_key = f"q{idx}"
    picked = st.radio("選択肢を選んでください：", labeled_choices, index=None, key=radio_key)

    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    elapsed = time.time() - st.session_state.start_times[idx]
    remaining = max(0, int(DEFAULT_TIME_LIMIT - elapsed))
    st.info(f"⏳ 残り時間：{remaining} 秒")

    if remaining <= 0:
        st.error("⌛ 時間切れ！未回答として進みます")
        st.session_state.answers[idx] = None
        st.session_state.stage = "explanation"
        st.rerun()
        st.stop()

    if st.button("回答する"):
        if picked:
            st.session_state.answers[idx] = labels[labeled_choices.index(picked)]
            st.session_state.stage = "explanation"
            st.rerun()
            st.stop()
        else:
            st.warning("選択肢を選んでください。")
    else:
        time.sleep(1)
        st.rerun()
        st.stop()

def draw_explanation(q, idx, choices, labels):
    user = st.session_state.answers[idx]
    correct = str(q['answer']).lower().strip()
    correct_idx = labels.index(correct) if correct in labels else -1
    correct_txt = choices[correct_idx] if correct_idx >= 0 else "不明"
    user_txt = choices[labels.index(user)] if user in labels else "未回答"

    if user == correct:
        st.success("✅ 正解！")
    elif user is None:
        st.error("⏱ 未回答")
    else:
        st.error("❌ 不正解")

    st.markdown(f"**正解：{correct.upper()} - {correct_txt}**")
    if q.get("explanation"):
        st.info(f"📘 解説：{q['explanation']}")

    if st.button("次の問題へ"):
        st.session_state.q_index += 1
        st.session_state.stage = "quiz"
        for k in list(st.session_state.keys()):
            if k.startswith(f"q{idx}"):
                del st.session_state[k]
        st.rerun()
        st.stop()

# ===== 選択画面 =====
if st.session_state.page == "select":
    st.title("SPI試験対策")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    st.session_state.temp_num_questions = st.number_input("出題数（最大50問）", 1, 50, value=20)
    st.session_state.temp_mode = st.radio("採点方法を選んでください：", ["最後にまとめて採点", "その都度採点"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.num_questions = st.session_state.temp_num_questions
        st.session_state.mode = st.session_state.temp_mode
        df = load_questions()
        filtered = df[df["category"] == st.session_state.category]
        st.session_state.questions = filtered.sample(n=st.session_state.num_questions).reset_index(drop=True)
        st.session_state.answers = [None] * st.session_state.num_questions
        st.session_state.start_times = [None] * st.session_state.num_questions
        st.session_state.q_index = 0
        st.session_state.stage = "quiz"
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

# ===== クイズ進行画面 =====
if st.session_state.page == "quiz":
    questions = st.session_state.questions
    idx = st.session_state.q_index
    if idx >= st.session_state.num_questions:
        st.session_state.page = "result"
        st.rerun()

    q = questions.iloc[idx]
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [q.get(f'choice{i+1}', "") for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    st.title(f"SPI模擬試験 Q{idx+1}/{st.session_state.num_questions}")
    st.subheader(q["question"])

    if st.session_state.stage == "quiz":
        draw_quiz(q, idx, choices, labeled_choices, labels)
    elif st.session_state.stage == "explanation":
        draw_explanation(q, idx, choices, labels)

# ===== 結果ページ =====
if st.session_state.page == "result":
    st.title("📊 結果発表")
    score = 0
    labels = ['a', 'b', 'c', 'd', 'e']
    for i, q in st.session_state.questions.iterrows():
        user = st.session_state.answers[i]
        correct = str(q['answer']).lower().strip()
        correct_bool = user == correct
        choices = [str(q.get(f'choice{j+1}', "")) for j in range(5)]
        user_txt = choices[labels.index(user)] if user in labels else "未回答"
        correct_txt = choices[labels.index(correct)] if correct in labels else "不明"

        st.markdown(f"**Q{i+1}: {q['question']}** {'✅' if correct_bool else '❌'}")
        st.markdown(f"あなたの回答：{user.upper() if user else '未回答'} - {user_txt}")
        st.markdown(f"正解：{correct.upper()} - {correct_txt}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")
        if correct_bool:
            score += 1

    st.success(f"🎯 最終スコア：{score} / {st.session_state.num_questions}")
    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            if k not in ["authenticated"]:
                del st.session_state[k]
        st.rerun()
