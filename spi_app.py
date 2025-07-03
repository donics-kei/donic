import streamlit as st
import pandas as pd
import time
import os

DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "spi_questions_converted.csv")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()
    df["question"] = df["question"].astype(str).str.strip()
    df = df[df["question"] != ""]
    return df

# 初期化
for k, v in {
    "page": "select",
    "q_index": 0,
    "stage": "quiz",
    "answers": [],
    "start_times": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# セッション復元（questionsが消えたとき）
if st.session_state.page != "select" and "questions" not in st.session_state:
    try:
        df = load_questions()
        cat = st.session_state.get("category", "言語")
        num = st.session_state.get("num_questions", 20)
        st.session_state.questions = df[df["category"] == cat].sample(n=num).reset_index(drop=True)
        st.warning("⚠️ セッション切れのため問題を復元しました。")
    except:
        st.session_state.page = "select"
        st.rerun()
        st.stop()

# クイズ描画
def render_quiz(q, idx, choices, labeled, labels):
    picked = st.radio("選択肢を選んでください：", labeled, key=f"q{idx}", index=None)

    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    remaining = max(0, int(DEFAULT_TIME_LIMIT - (time.time() - st.session_state.start_times[idx])))
    st.info(f"⏳ 残り時間：{remaining} 秒")

    if remaining <= 0:
        st.error("⌛ 時間切れ")
        st.session_state.answers[idx] = None
        st.session_state.stage = "explanation"
        st.rerun()
        st.stop()

    if st.button("回答する"):
        if picked:
            st.session_state.answers[idx] = labels[labeled.index(picked)]
            st.session_state.stage = "explanation"
            st.rerun()
            st.stop()
        else:
            st.warning("選択肢を選んでください。")
    else:
        time.sleep(1)
        st.rerun()
        st.stop()

# 解説描画
def render_explanation(q, idx, choices, labels):
    user = st.session_state.answers[idx]
    correct = str(q["answer"]).lower().strip()
    ci = labels.index(correct) if correct in labels else -1
    correct_txt = choices[ci] if ci >= 0 else "不明"
    ui = labels.index(user) if user in labels else -1
    user_txt = choices[ui] if ui >= 0 else "未回答"

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
        qkey = f"q{idx}"
        if qkey in st.session_state:
            del st.session_state[qkey]
        st.rerun()
        st.stop()

# 描画切替
def render_current_stage():
    idx = st.session_state.q_index
    q = st.session_state.questions.iloc[idx]
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [q.get(f"choice{i+1}", "") for i in range(5)]
    labeled = [f"{l}. {c}" for l, c in zip(labels, choices)]

    text = str(q.get("question", "")).strip()
    if text:
        st.subheader(text)
    else:
        st.error("❗ この問題は空欄です。")
        st.json(q.to_dict())
        st.stop()

    if st.session_state.stage == "quiz":
        render_quiz(q, idx, choices, labeled, labels)
    elif st.session_state.stage == "explanation":
        render_explanation(q, idx, choices, labels)

# 選択画面
if st.session_state.page == "select":
    st.title("SPI模擬試験")
    st.session_state.temp_category = st.radio("出題カテゴリー：", ["言語", "非言語"])
    st.session_state.temp_num_questions = st.number_input("出題数（1〜50）", 1, 50, value=20)
    st.session_state.temp_mode = st.radio("採点方法：", ["その都度採点", "最後にまとめて採点"])
    if st.button("開始"):
        df = load_questions()
        st.session_state.category = st.session_state.temp_category
        st.session_state.num_questions = st.session_state.temp_num_questions
        st.session_state.mode = st.session_state.temp_mode
        st.session_state.questions = df[df["category"] == st.session_state.category].sample(
            n=st.session_state.num_questions).reset_index(drop=True)
        st.session_state.answers = [None] * st.session_state.num_questions
        st.session_state.start_times = [None] * st.session_state.num_questions
        st.session_state.q_index = 0
        st.session_state.stage = "quiz"
        st.session_state.page = "quiz"
        st.rerun()
        st.stop()
    st.stop()

# 出題画面
if st.session_state.page == "quiz":
    if st.session_state.q_index >= st.session_state.num_questions:
        st.session_state.page = "result"
        st.rerun()
        st.stop()
    st.title(f"Q{st.session_state.q_index + 1}/{st.session_state.num_questions}")
    render_current_stage()

# 結果画面
if st.session_state.page == "result":
    st.title("📊 結果発表")
    score = 0
    labels = ['a', 'b', 'c', 'd', 'e']
    for i, q in st.session_state.questions.iterrows():
        user = st.session_state.answers[i]
        correct = str(q["answer"]).lower().strip()
        correct_bool = user == correct
        choices = [q.get(f"choice{j+1}", "") for j in range(5)]
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

    st.success(f"🎯 スコア：{score} / {st.session_state.num_questions}")
    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            if k not in ["authenticated"]:
                del st.session_state[k]
        st.rerun()
        st.stop()

