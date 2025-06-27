import streamlit as st
import pandas as pd
import os

st.title("SPI 最小テスト")

@st.cache_data
def load_questions():
    csv_path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(csv_path):
        st.error("CSVファイル 'spi_questions_converted.csv' が見つかりません")
        st.stop()
    return pd.read_csv(csv_path)

df = load_questions()
if df.empty:
    st.warning("CSVファイルに問題が含まれていません。")
    st.stop()

# 1問だけ出題
question = df.iloc[0]
st.subheader(f"Q: {question['question']}")

choices = [str(question[f'choice{i+1}']) for i in range(5)]
labels = ['a', 'b', 'c', 'd', 'e']
labeled_choices = [f"{l}. {c}" for l, c in zip(labels, choices)]

selected = st.radio("選択肢を選んでください：", labeled_choices)

if st.button("回答する"):
    selected_index = labeled_choices.index(selected)
    selected_label = labels[selected_index]
    correct_answer = str(question['answer']).lower().strip()

    if selected_label == correct_answer:
        st.success("正解です！")
    else:
        st.error(f"不正解。正解は {correct_answer.upper()}")

    if question.get("explanation"):
        st.info(f"解説：{question['explanation']}")
