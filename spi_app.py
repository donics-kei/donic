import streamlit as st
import pandas as pd
import time
import os

DEFAULT_TIME_LIMIT = 60  # デフォルトの時間制限（秒）

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

if "page" not in st.session_state:
    st.session_state.page = "select"

# 初期画面
if st.session_state.page == "select":
    st.title("SPI模擬試験：採点モード選択式")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    st.session_state.temp_num_questions = st.number_input("出題数を入力してください（最大50問）", min_value=1, max_value=50, value=20, step=1)
    st.session_state.temp_mode = st.radio("採点方法を選んでください：", ["最後にまとめて採点", "その都度採点"])
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.num_questions = st.session_state.temp_num_questions
        st.session_state.mode = st.session_state.temp_mode
        df = load_questions()
        filtered_df = df[df['category'] == st.session_state.category]
        sample_size = min(st.session_state.num_questions, len(filtered_df))
        st.session_state.questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
        st.session_state.answers = [None] * sample_size
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * sample_size
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

questions = st.session_state.questions
q_index = st.session_state.q_index
num_questions = st.session_state.num_questions

# タイトル表示
st.title(f"SPI模擬試験（{st.session_state.category}・{num_questions}問）")

if q_index < num_questions:
    q = questions.iloc[q_index]
    time_limit_col = 'time_limit' if 'time_limit' in q else 'time_limt'
    try:
        question_time_limit = int(q.get(time_limit_col, DEFAULT_TIME_LIMIT))
    except:
        question_time_limit = DEFAULT_TIME_LIMIT

    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = int(question_time_limit - elapsed)
    if remaining < 0:
        remaining = 0
    st.warning(f"⏳ 残り時間：{remaining} 秒")

    if remaining == 0:
        st.error("時間切れ！未回答として次へ進みます")
        st.session_state.q_index += 1
        st.rerun()

    st.subheader(f"Q{q_index+1}: {q['question']}")
    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [str(q[f'choice{i+1}']) for i in range(5)]
    labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
    selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{q_index}")

    if st.button("次へ"):
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

            if st.button("次の問題へ"):
                st.session_state.q_index += 1
                st.rerun()
        else:
            st.session_state.q_index += 1
            st.rerun()

    time.sleep(1)
    st.rerun()

else:
    # 採点処理
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
        your_choice = choices[labels.index(your_answer)] if your_answer in labels else None
        correct = your_answer == correct_answer
        if correct:
            score += 1
        results.append({
            "question": q['question'],
            "your_answer": your_answer,
            "your_choice": your_choice,
            "correct_answer": correct_answer,
            "correct_choice": correct_choice,
            "correct": correct,
            "explanation": q.get("explanation", "")
        })

    st.subheader(f"🎯 最終スコア：{score} / {num_questions}")
    st.success("全問終了！ 以下が採点結果です：")
    st.subheader("採点結果と解説")
    for i, r in enumerate(results):
        if r['correct']:
            st.markdown(f"**Q{i+1}: {r['question']}** ✅ 正解")
        else:
            st.markdown(f"**Q{i+1}: {r['question']}** ❌ 不正解")

        if r['your_answer']:
            st.markdown(f"あなたの回答：{r['your_answer'].upper()} - {r['your_choice']}")
        else:
            st.markdown("あなたの回答：未回答")

        st.markdown(f"正解：{r['correct_answer'].upper()} - {r['correct_choice']}")
        if r['explanation']:
            st.markdown(f"📘 解説：{r['explanation']}")
        st.markdown("---")

    if st.button("もう一度解く"):
        del st.session_state.page
        st.rerun()
