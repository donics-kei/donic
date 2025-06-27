import streamlit as st
import pandas as pd
import time
import os
st.set_page_config(page_title="SPI 言語演習", layout="centered")

# ロゴとCSSスタイル
st.markdown("""
    <style>
        body {
            background-color: #E0F7FA;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stRadio > div {
            flex-direction: column;
        }
        .stButton > button {
            width: 100%;
            font-size: 1.1rem;
        }
    </style>
""", unsafe_allow_html=True)

# ロゴはカラム幅に合わせる
st.image("nics_logo.png", use_column_width=True)

# 背景とロゴ
st.markdown('<style>body { background-color: #E0F7FA; }</style>', unsafe_allow_html=True)
st.image("nics_logo.png", width=300)

DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# ページ切り替え用セッション変数
if "page" not in st.session_state:
    st.session_state.page = "start"

# ========== START ページ ==========
if st.session_state.page == "start":
    st.title("SPI試験対策：言語分野（20問）")
    st.markdown("このアプリでは、SPI言語分野の模擬演習を行うことができます。")
    st.markdown("- 各問題には時間制限があります")
    st.markdown("- 回答後すぐに正解・解説が表示されます")
    st.markdown("- 全問終了後にスコアが表示されます")
    
    if st.button("演習スタート"):
        df = load_questions()
        filtered = df[df['category'] == "言語"]
        st.session_state.questions = filtered.sample(min(20, len(filtered))).reset_index(drop=True)
        st.session_state.answers = [None] * 20
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * 20
        st.session_state.page = "quiz"
        st.rerun()

# ========== QUIZ ページ ==========
elif st.session_state.page == "quiz":
    questions = st.session_state.questions
    q_index = st.session_state.q_index
    num_questions = len(questions)

    if q_index >= num_questions:
        st.session_state.page = "result"
        st.rerun()

    q = questions.iloc[q_index]
    time_limit = int(q.get("time_limit", DEFAULT_TIME_LIMIT))

    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = int(time_limit - elapsed)
    remaining = max(0, remaining)

    feedback_key = f"feedback_shown_{q_index}"
    if remaining == 0 and not st.session_state.get(feedback_key, False):
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.rerun()

    st.title(f"Q{q_index + 1} / {num_questions}")
    st.warning(f"⏳ 残り時間：{remaining} 秒")
    st.subheader(q['question'])

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q[f'choice{i+1}']) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    feedback_container = st.empty()

    if not st.session_state.get(feedback_key, False):
        selected = st.radio("選択肢を選んでください：", labeled_choices, index=None, key=f"selection_{q_index}")

        if st.button("回答する") and selected:
            selected_index = labeled_choices.index(selected)
            st.session_state.answers[q_index] = labels[selected_index]
            correct_answer = str(q['answer']).lower().strip()
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

# ========== RESULT ページ ==========
elif st.session_state.page == "result":
    questions = st.session_state.questions
    answers = st.session_state.answers
    score = 0

    st.title("📊 採点結果")

    for i, q in questions.iterrows():
        your_answer = answers[i]
        correct_answer = str(q['answer']).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q[f'choice{j+1}']) for j in range(5)]
        try:
            correct_index = labels.index(correct_answer)
        except ValueError:
            correct_index = -1
        correct_choice = choices[correct_index] if correct_index != -1 else "不明"
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

    if st.button("もう一度解く"):
        st.session_state.page = "start"
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.q_index = 0
        st.session_state.start_times = []
        for k in list(st.session_state.keys()):
            if k.startswith("feedback_") or k.startswith("selection_") or k.startswith("feedback_shown_"):
                del st.session_state[k]
        st.rerun()

