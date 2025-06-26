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

if "page" not in st.session_state:
    st.session_state.page = "select"
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False

if st.session_state.page == "select":
    st.title("SPI試験対策")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    st.session_state.temp_num_questions = st.number_input("出題数を入力してください（最大50問）", 1, 50, 20, 1)
    st.session_state.temp_mode = st.radio("採点方法を選んでください：", ["最後にまとめて採点", "その都度採点"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.num_questions = st.session_state.temp_num_questions
        df = load_questions()
        filtered = df[df['category'] == st.session_state.category]
        st.session_state.questions = filtered.sample(min(len(filtered), st.session_state.num_questions)).reset_index(drop=True)
        st.session_state.answers = [None] * st.session_state.num_questions
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * st.session_state.num_questions
        st.session_state.mode = st.session_state.temp_mode
        st.session_state.page = "quiz"
        st.session_state.feedback_shown = False
        st.rerun()
    st.stop()

questions = st.session_state.questions
q_index = st.session_state.q_index
num_questions = st.session_state.num_questions

st.title(f"SPI模擬試験（{st.session_state.category}・{num_questions}問）")

if q_index < num_questions:
    q = questions.iloc[q_index]
    time_limit_col = 'time_limit' if 'time_limit' in q else 'time_limt'
    try:
        time_limit = int(q.get(time_limit_col, DEFAULT_TIME_LIMIT))
    except:
        time_limit = DEFAULT_TIME_LIMIT

    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = int(time_limit - elapsed)
    if remaining < 0:
        remaining = 0
    st.warning(f"⏳ 残り時間：{remaining} 秒")

    if remaining == 0 and not st.session_state.feedback_shown:
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.session_state.feedback_shown = False
        st.rerun()

    st.subheader(f"Q{q_index + 1}: {q['question']}")
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q[f'choice{i+1}']) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
    selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{q_index}")

    if not st.session_state.feedback_shown:
        if st.button("回答する"):
            selected_index = labeled_choices.index(selected)
            st.session_state.answers[q_index] = labels[selected_index]
            if st.session_state.mode == "その都度採点":
                correct_answer = str(q['answer']).lower().strip()
                correct = st.session_state.answers[q_index] == correct_answer
                correct_choice = choices[labels.index(correct_answer)] if correct_answer in labels else "不明"
                your_choice = choices[selected_index]

                if correct:
                    st.success("正解！")
                else:
                    st.error("不正解")

                st.markdown(f"あなたの回答：{labels[selected_index].upper()} - {your_choice}")
                st.markdown(f"正解：{correct_answer.upper()} - {correct_choice}")
                if q.get("explanation"):
                    st.info(f"📘 解説：{q['explanation']}")
                st.session_state.feedback_shown = True
            else:
                st.session_state.q_index += 1
                st.rerun()
    else:
        if st.button("次の問題へ"):
            st.session_state.q_index += 1
            st.session_state.feedback_shown = False
            st.rerun()

    time.sleep(1)
    st.rerun()

else:
    st.subheader("採点結果")
    score = 0
    results = []
    for i, q in questions.iterrows():
        your_answer = st.session_state.answers[i]
        correct_answer = str(q['answer']).lower().strip()
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q[f'choice{j+1}']) for j in range(5)]
        try:
            correct_index = labels.index(correct_answer)
        except ValueError:
            correct_index = -1
        correct_choice = choices[correct_index] if correct_index != -1 else "不明"
        your_choice = choices[labels.index(your_answer)] if your_answer in labels else "未回答"
        correct = your_answer == correct_answer
        if correct:
            score += 1
        results.append((i + 1, q['question'], your_answer, your_choice, correct_answer, correct_choice, correct, q.get("explanation", "")))

    st.success(f"🎯 最終スコア：{score} / {num_questions}")
    for i, question, ya, yc, ca, cc, correct, exp in results:
        st.markdown(f"**Q{i}: {question}** {'✅ 正解' if correct else '❌ 不正解'}")
        st.markdown(f"あなたの回答：{ya.upper() if ya else '未回答'} - {yc}")
        st.markdown(f"正解：{ca.upper()} - {cc}")
        if exp:
            st.markdown(f"📘 解説：{exp}")
        st.markdown("---")

    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
