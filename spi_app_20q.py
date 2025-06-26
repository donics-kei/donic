import streamlit as st
import pandas as pd
import time
import os

@st.cache_data
def load_questions():
    BASE_DIR = os.path.dirname(__file__)
    csv_path = os.path.join(BASE_DIR, "spi_questions_converted.csv")
    return pd.read_csv(csv_path)

# ページ管理
if "page" not in st.session_state:
    st.session_state.page = "select"

# 空白ページ → 次の問題へ遷移時に一瞬表示
if st.session_state.page == "blank":
    st.empty()
    time.sleep(0.1)
    st.session_state.page = "quiz"
    st.rerun()

# 初期化画面
if st.session_state.page == "select":
    st.title("SPI演習：1問ずつ採点・任意の問題数")
    st.session_state.temp_category = st.radio("出題カテゴリーを選んでください：", ["言語", "非言語"])
    st.session_state.temp_num_questions = st.number_input("出題数を入力してください（最大50問）", min_value=1, max_value=50, value=20)
    if st.button("開始"):
        st.session_state.category = st.session_state.temp_category
        st.session_state.num_questions = st.session_state.temp_num_questions
        df = load_questions()
        filtered_df = df[df['category'] == st.session_state.category]
        sample_size = min(st.session_state.num_questions, len(filtered_df))
        st.session_state.questions = filtered_df.sample(n=sample_size).reset_index(drop=True)
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.answered = []
        st.session_state.start_times = [None] * sample_size
        st.session_state.page = "quiz"
        st.rerun()
    st.stop()

# 問題処理開始
questions = st.session_state.questions
q_index = st.session_state.q_index
num_questions = st.session_state.num_questions

# 時間制限取得
time_limit_col = 'time_limit' if 'time_limit' in questions.columns else 'time_limt'
time_limits = questions[time_limit_col].fillna(60).astype(int).tolist()

st.title(f"SPI模擬試験（{st.session_state.category}・{num_questions}問）")

if q_index < num_questions:
    q = questions.iloc[q_index]
    time_limit = time_limits[q_index]

    # 時間カウント初期化
    if st.session_state.start_times[q_index] is None:
        st.session_state.start_times[q_index] = time.time()

    elapsed = time.time() - st.session_state.start_times[q_index]
    remaining = int(time_limit - elapsed)
    if remaining < 0:
        remaining = 0

    # タイマー表示
    timer_placeholder = st.empty()
    timer_placeholder.warning(f"⏳ 残り時間：{remaining} 秒")

    # 問題文表示
    st.subheader(f"Q{q_index+1}: {q['question']}")

    if remaining == 0 and not st.session_state.get(f"feedback_shown_{q_index}", False):
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
        st.session_state.page = "blank"
        st.rerun()

    # 選択肢表示・回答処理
    if not st.session_state.get(f"feedback_shown_{q_index}", False):
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q[f'choice{i+1}']) for i in range(5)]
        labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

        selected = st.radio("選択肢を選んでください：", labeled_choices, key=f"q{q_index}")
        if st.button("回答する"):
            st.session_state[f"selected_choice_{q_index}"] = selected
            st.session_state[f"feedback_shown_{q_index}"] = True
            st.rerun()

        time.sleep(1)
        st.rerun()

    else:
        labels = ['a', 'b', 'c', 'd', 'e']
        choices = [str(q[f'choice{i+1}']) for i in range(5)]
        labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]
        selected_choice_key = f"selected_choice_{q_index}"
        selected_index = labeled_choices.index(st.session_state[selected_choice_key])
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

        if st.button("次の問題へ"):
            st.session_state.pop(f"feedback_shown_{q_index}", None)
            st.session_state.pop(f"selected_choice_{q_index}", None)
            st.session_state.q_index += 1
            st.session_state.page = "blank"
            st.rerun()

else:
    st.success("✅ すべての問題が終了しました！")
    st.metric("あなたの最終スコア", f"{st.session_state.score} / {num_questions}")
    st.markdown("---")
    st.subheader("詳細結果：")
    df_result = pd.DataFrame(st.session_state.answered)
    df_result.index = [f"Q{i+1}" for i in range(len(df_result))]
    st.dataframe(df_result)

    if st.button("もう一度解く"):
        del st.session_state.page
        st.rerun()
