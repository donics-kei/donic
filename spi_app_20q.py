import streamlit as st
import pandas as pd
import time
import os
import random

st.set_page_config(page_title="SPI言語20問", layout="centered")

# スタイル（スマホ対応）
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ロゴ
if os.path.exists("nics_logo.png"):
    st.image("nics_logo.png", width=260)

@st.cache_data
def load_questions():
    path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(path):
        st.error("CSVが見つかりません。")
        st.stop()
    df = pd.read_csv(path)
    df["time_limit"] = df["time_limit"].fillna(60)
    return df

# ログイン処理
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("ログイン")
    username = st.text_input("ユーザーID")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if username == "nics" and password == "nagasaki2025":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("ユーザーIDまたはパスワードが違います。")
    st.stop()

# 初期ページ設定
if "page" not in st.session_state:
    st.session_state.page = "start"

if st.session_state.page == "start":
    st.title("SPI言語演習（20問ランダム）")
    st.markdown("- 制限時間あり\n- 回答後に即時解説\n- スコア表示")

    if st.button("演習スタート"):
        df = load_questions()
        filtered = df[df["category"].str.strip() == "言語"]
        if len(filtered) < 20:
            st.error("「言語」カテゴリの問題が20問未満です。")
            st.stop()
        selected = filtered.sample(n=20).reset_index(drop=True)
        st.session_state.questions = selected
        st.session_state.answers = [None] * 20
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * 20
        st.session_state.page = "quiz"
        st.rerun()

elif st.session_state.page == "quiz":
    idx = st.session_state.q_index
    if idx >= 20:
        st.session_state.page = "result"
        st.rerun()

    q = st.session_state.questions.iloc[idx]
    st.header(f"Q{idx+1}/20")
    st.markdown(f"**{q['question']}**")

    labels = ["a", "b", "c", "d", "e"]
    choices = [q.get(f"choice{i+1}", "") for i in range(5)]
    choice_map = {f"{l}. {c}": l for l, c in zip(labels, choices)}
    picked = st.radio("選択肢を選んでください：", list(choice_map.keys()), index=None, key=f"choice_{idx}")

    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    remaining = int(q.get("time_limit", 60) - (time.time() - st.session_state.start_times[idx]))
    st.info(f"残り時間：{remaining}秒")

    if remaining <= 0:
        st.error("時間切れ！")
        st.session_state.answers[idx] = None
        st.session_state.q_index += 1
        st.rerun()

    if picked and st.button("回答する"):
        sel = choice_map[picked]
        st.session_state.answers[idx] = sel
        correct = str(q["answer"]).lower().strip()
        correct_index = labels.index(correct) if correct in labels else -1
        st.subheader("解答結果")
        if sel == correct:
            st.success("正解！")
        else:
            st.error("不正解")
        if correct_index >= 0:
            st.markdown(f"正解：{correct.upper()} - {choices[correct_index]}")
        if q.get("explanation"):
            st.info(f"📘 解説：{q['explanation']}")
        if st.button("次へ"):
            st.session_state.q_index += 1
            st.rerun()
    else:
        time.sleep(1)
        st.rerun()

elif st.session_state.page == "result" or st.session_state.q_index >= 20:
    st.title("📊 結果発表")
    score = 0
    for i, q in st.session_state.questions.iterrows():
        your = st.session_state.answers[i]
        answer = str(q["answer"]).lower().strip()
        correct = (your == answer)
        labels = ["a", "b", "c", "d", "e"]
        choices = [q.get(f"choice{j+1}", "") for j in range(5)]
        your_txt = choices[labels.index(your)] if your in labels else "未回答"
        correct_txt = choices[labels.index(answer)] if answer in labels else "不明"
        st.markdown(f"**Q{i+1}: {q['question']}** {'✅' if correct else '❌'}")
        st.markdown(f"あなたの回答：{your.upper() if your else '未回答'} - {your_txt}")
        st.markdown(f"正解：{answer.upper()} - {correct_txt}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")
        if correct:
            score += 1

    st.success(f"🎯 最終スコア：{score}/20")

    if st.button("もう一度挑戦"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
