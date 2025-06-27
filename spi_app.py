import streamlit as st
import pandas as pd
import time
import os

st.markdown('<style>body { background-color: #E0F7FA; }</style>', unsafe_allow_html=True)
st.image("nics_logo.png", width=300)

DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# セッション初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "cleared_feedback" not in st.session_state:
    st.session_state.cleared_feedback = False

# SELECT PAGE
if st.session_state.page == "select":
    st.title("SPI試験対策")
    category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    num_q = st.number_input("出題数を入力してください（最大50問）", 1, 50, 20, 1)
    mode = st.radio("採点方法を選んでください：", ["最後にまとめて採点", "その都度採点"])
    
    if st.button("開始"):
        df = load_questions()
        filtered = df[df["category"] == category]
        st.session_state.questions = filtered.sample(min(len(filtered), num_q)).reset_index(drop=True)
        st.session_state.answers = [None] * num_q
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * num_q
        st.session_state.category = category
        st.session_state.num_questions = num_q
        st.session_state.mode = mode
        st.session_state.page = "quiz"
        st.session_state.feedback_shown = False
        st.rerun()

    st.stop()

# QUIZ PAGE
questions = st.session_state.questions
q_index = st.session_state.q_index
num_questions = st.session_state.num_questions

if q_index < num_questions:
    q = questions.iloc[q_index]
    time_limit = int(q.get("time_limit", DEFAULT_TIME_LIMIT))

    # 残り時間の計算
    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()
    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = max(0, int(time_limit - elapsed))
    st.warning(f"⏳ 残り時間：{remaining} 秒")

    if remaining == 0 and not st.session_state.feedback_shown:
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.session_state.feedback_shown = False
        st.session_state.cleared_feedback = True
        st.rerun()

    st.subheader(f"Q{q_index + 1}: {q['question']}")
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q[f'choice{i+1}']) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

    feedback_container = st.empty()

    if not st.session_state.feedback_shown:
        selected = st.radio("選択肢を選んでください：", labeled_choices, index=None, key=f"choice_{q_index}")
        if st.button("回答する") and selected:
            selected_index = labeled_choices.index(selected)
            selected_label = labels[selected_index]
            st.session_state.answers[q_index] = selected_label

            if st.session_state.mode == "その都度採点":
                correct_answer = str(q['answer']).lower().strip()
                correct = selected_label == correct_answer
                correct_choice = choices[labels.index(correct_answer)] if correct_answer in labels else "不明"
                your_choice = choices[selected_index]

                with feedback_container.container():
                    if correct:
                        st.success("正解！")
                    else:
                        st.error("不正解")
                    st.markdown(f"あなたの回答：{selected_label.upper()} - {your_choice}")
                    st.markdown(f"正解：{correct_answer.upper()} - {correct_choice}")
                    if q.get("explanation"):
                        st.info(f"📘 解説：{q['explanation']}")

                st.session_state.feedback_shown = True
    else:
        if st.button("次の問題へ"):
            feedback_container.empty()
            st.session_state.q_index += 1
            st.session_state.feedback_shown = False
            st.session_state.cleared_feedback = True
            st.session_state.pop(f"choice_{q_index}", None)
            st.rerun()

    # カウントダウン更新（フィードバックが表示中でない場合のみ）
    if not st.session_state.feedback_shown:
        time.sleep(1)
        st.rerun()

# RESULT PAGE
else:
    st.subheader("採点結果")
    score = 0
    for i, q in questions.iterrows():
        your_answer = st.session_state.answers[i]
        correct_answer = str(q['answer']).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q[f'choice{j+1}']) for j in range(5)]
        correct_choice = choices[labels.index(correct_answer)] if correct_answer in labels else "不明"
        your_choice = choices[labels.index(your_answer)] if your_answer in labels else "未回答"
        correct = your_answer == correct_answer
        if correct:
            score += 1

        st.markdown(f"**Q{i+1}: {q['question']}** {'✅ 正解' if correct else '❌ 不正解'}")
        st.markdown(f"あなたの回答：{your_answer.upper() if your_answer else '未回答'} - {your_choice}")
        st.markdown(f"正解：{correct_answer.upper()} - {correct_choice}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")

    st.success(f"🎯 最終スコア：{score} / {num_questions}")

    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
