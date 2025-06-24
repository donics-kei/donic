import streamlit as st
import pandas as pd
import time
import os

NUM_QUESTIONS = 20
DEFAULT_TIME_LIMIT = 60

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# 初期化
if "page" not in st.session_state:
    st.session_state.page = "select"
if st.session_state.page == "select":
    st.title("SPI模擬試験：1問ずつ採点・20問版")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        df = load_questions()
        filtered_df = df[df['category'] == st.session_state.category]
        sample_size = min(NUM_QUESTIONS, len(filtered_df))
        st.session_state.questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.answered = []
        st.session_state.start_times = [None] * sample_size
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

questions = st.session_state.questions
q_index = st.session_state.q_index

st.title(f"SPI模擬試験（{st.session_state.category}・{NUM_QUESTIONS}問）")

if q_index < NUM_QUESTIONS:
    q = questions.iloc[q_index]
    if not st.session_state.get("feedback_shown", False):
        st.subheader(f"Q{q_index + 1}: {q['question']}")

        # カウントダウン表示
        if st.session_state.start_times[q_index] is None:
            st.session_state.start_times[q_index] = time.time()

        elapsed = time.time() - st.session_state.start_times[q_index]
        remaining = int(q.get("time_limt", 60) - elapsed)
        if remaining < 0:
            remaining = 0

        st.warning(f"⏳ 残り時間：{remaining} 秒")

        if remaining == 0 and len(st.session_state.answered) <= q_index:
            st.session_state.answered.append({
                "question": q['question'],
                "your_answer": None,
                "your_choice": None,
                "correct_answer": str(q['answer']).lower().strip(),
                "correct_choice": q[f"choice{ord(str(q['answer']).lower().strip()) - 96}"],
                "correct": False,
                "explanation": q.get("explanation", "")
            })
            st.session_state.q_index += 1
            st.session_state.feedback_shown = False
            st.session_state.selected_choice = None
            st.rerun()

        time.sleep(1)
        st.rerun()
        

        time.sleep(1)
        st.rerun()

    labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
        labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
        selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{q_index}")
        if st.button("回答する"):
            st.session_state.selected_choice = selected
            st.session_state.feedback_shown = True
            st.rerun()
    else:
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
        labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
        selected = None
        if st.session_state.get("selected_choice"):
            labels = ['a', 'b', 'c', 'd', 'e']
            choices = [str(q['choice1']), str(q['choice2']), str(q['choice3']), str(q['choice4']), str(q['choice5'])]
            labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
            selected_index = labeled_choices.index(st.session_state["selected_choice"])
            your_answer = labels[selected_index]
            correct_answer = str(q['answer']).lower().strip()
            correct_index = labels.index(correct_answer)
            is_correct = your_answer == correct_answer
            your_choice = choices[selected_index]
            correct_choice = choices[correct_index]

            if is_correct:
                st.success("正解！")
                st.session_state.score += 1
            else:
                st.error("不正解")

            st.markdown(f"**あなたの回答：{your_answer.upper()} - {your_choice}**")
            st.markdown(f"**正解：{correct_answer.upper()} - {correct_choice}**")
            if q.get("explanation"):
                st.info(f"📘 解説：{q['explanation']}")

            if len(st.session_state.answered) <= q_index:
                st.session_state.answered.append({
                    "question": q['question'],
                    "your_answer": your_answer,
                    "your_choice": your_choice,
                    "correct_answer": correct_answer,
                    "correct_choice": correct_choice,
                    "correct": is_correct,
                    "explanation": q.get("explanation", "")
                })

        
        # カウントダウン表示
        if st.session_state.start_times[q_index] is None:
            st.session_state.start_times[q_index] = time.time()

        elapsed = time.time() - st.session_state.start_times[q_index]
        remaining = int(q.get("time_limt", 60) - elapsed)
        if remaining < 0:
            remaining = 0

        st.warning(f"⏳ 残り時間：{remaining} 秒")

        if remaining == 0 and len(st.session_state.answered) <= q_index:
            st.session_state.answered.append({
                "question": q['question'],
                "your_answer": None,
                "your_choice": None,
                "correct_answer": str(q['answer']).lower().strip(),
                "correct_choice": q[f"choice{ord(str(q['answer']).lower().strip()) - 96}"],
                "correct": False,
                "explanation": q.get("explanation", "")
            })
            st.session_state.q_index += 1
            st.session_state.feedback_shown = False
            st.session_state.selected_choice = None
            st.rerun()

        time.sleep(1)
        st.rerun()

        if st.session_state.get("feedback_shown", False) and st.session_state.get("selected_choice"):
            if st.button("次の問題へ"):
                st.session_state.q_index += 1
                st.session_state.feedback_shown = False
                st.session_state.selected_choice = None
                st.rerun()
