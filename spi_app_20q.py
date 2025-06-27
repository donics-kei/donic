import streamlit as st
import pandas as pd
import time
import os

# ロゴの表示と背景色
st.markdown('<style>body { background-color: #E0F7FA; }</style>', unsafe_allow_html=True)
st.image("nics_logo.png", width=300)

DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# blankページで一度状態をリセット
if st.session_state.get("page") == "blank":
    keys_to_clear = [
        k for k in list(st.session_state.keys())
        if k.startswith("choice_")
        or k.startswith("feedback_shown_")
        or k.startswith("selected_choice_")
        or k.startswith("feedback_data_")
    ]
    for k in keys_to_clear:
        del st.session_state[k]
    st.session_state.page = "quiz"
    st.rerun()

# 初期化
if "page" not in st.session_state:
    st.session_state.page = "quiz"
    st.session_state.category = "言語"
    st.session_state.num_questions = 20
    df = load_questions()
    filtered = df[df['category'] == st.session_state.category]
    st.session_state.questions = filtered.sample(min(len(filtered), st.session_state.num_questions)).reset_index(drop=True)
    st.session_state.answers = [None] * st.session_state.num_questions
    st.session_state.q_index = 0
    st.session_state.start_times = [None] * st.session_state.num_questions
    st.session_state[f"feedback_shown_0"] = False

questions = st.session_state.questions
q_index = st.session_state.q_index
num_questions = st.session_state.num_questions

st.title(f"SPI試験対策（言語 20問）")

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

    feedback_key = f"feedback_shown_{q_index}"
    if remaining == 0 and not st.session_state.get(feedback_key, False):
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.answers[q_index] = None
        st.session_state.q_index += 1
        st.session_state.page = "blank"
        st.rerun()

    st.subheader(f"Q{q_index + 1}: {q['question']}")
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q[f'choice{i+1}']) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
    selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"choice_{q_index}")

    if not st.session_state.get(feedback_key, False):
        if st.button("回答する"):
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

        # ⏱ カウントダウン中だけ sleep & rerun
        time.sleep(1)
        st.rerun()  # カウントダウン中のみ

       elif st.session_state.get(feedback_key):
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
            placeholder = st.empty()
            placeholder.markdown("")
            keys_to_clear = [
                k for k in list(st.session_state.keys())
                if k.startswith("choice_")
                or k.startswith("feedback_shown_")
                or k.startswith("selected_choice_")
                or k.startswith("feedback_data_")
            ]
            for k in keys_to_clear:
                del st.session_state[k]
            time.sleep(0.2)
            st.session_state.q_index += 1
            st.session_state.page = "blank"
            st.rerun()

else:
    st.subheader("採点結果")
    score = 0
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
        correct_flag = your_answer == correct_answer
        if correct_flag:
            score += 1

        st.markdown(f"**Q{i+1}: {q['question']}** {'✅ 正解' if correct_flag else '❌ 不正解'}")
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
