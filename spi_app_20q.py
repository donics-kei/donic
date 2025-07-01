import streamlit as st
import pandas as pd
import time
import os
import random
import platform

st.set_page_config(page_title="SPI言語20問", layout="centered")

# スマホ判定（User-Agent参照）
user_agent = st.get_option("browser.user_agent") or ""
is_mobile = ("Android" in user_agent) or ("iPhone" in user_agent)
st.session_state["is_mobile"] = is_mobile

# スタイル調整（スマホ対応）
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ロゴ（任意）
if os.path.exists("nics_logo.png"):
    st.image("nics_logo.png", width=260)

@st.cache_data
def load_questions():
    path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(path):
        st.error("CSVファイルが見つかりません。")
        st.stop()
    df = pd.read_csv(path)
    df["time_limit"] = df["time_limit"].fillna(60)
    return df

# 認証状態を保持
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
            st.error("ユーザーIDまたはパスワードが間違っています。")
    st.stop()

# ページ管理
if "page" not in st.session_state:
    st.session_state.page = "start"

# ==== スタートページ ====
if st.session_state.page == "start":
    st.title("SPI言語演習（20問ランダム）")
    st.markdown("- 制限時間あり\n- 回答後に解説表示\n- スコア付き")

    if st.button("演習スタート"):
        df = load_questions()
        filtered = df[df["category"].str.strip() == "言語"]
        if len(filtered) < 20:
            st.error("「言語」カテゴリの問題が20問未満です。")
            st.stop()
        random.seed(time.time())
        selected = filtered.sample(n=20, random_state=random.randint(1, 999999)).reset_index(drop=True)
        st.session_state.questions = selected
        st.session_state.answers = [None] * 20
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * 20
        st.session_state.page = "quiz"
        st.rerun()

# ==== 出題ページ ====
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
    radio_key = f"picked_{idx}"
    picked = st.radio("選択肢を選んでください：", list(choice_map.keys()), index=None, key=radio_key)

    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    raw_limit = q.get("time_limit", 60)
    time_limit = 60 if pd.isna(raw_limit) else int(raw_limit)
    remaining = int(time_limit - (time.time() - st.session_state.start_times[idx]))

    feedback_key = f"feedback_shown_{idx}"
    st.info(f"⏱ 残り時間：{remaining} 秒")

    # --- スマホ用手動更新ボタン ---
    if is_mobile and not st.session_state.get(feedback_key, False):
        if st.button("⏳ 時間を更新する（スマホ用）"):
            st.rerun()

    if not st.session_state.get(feedback_key, False):
        if remaining <= 0:
            st.warning("⌛ 時間切れ！未回答として次へ進みます")
            st.session_state.answers[idx] = None
            st.session_state.q_index += 1
            for k in list(st.session_state.keys()):
                if k.startswith("picked_") or k.startswith("feedback_shown_"):
                    del st.session_state[k]
            st.rerun()
        elif not is_mobile:
            time.sleep(1)
            st.rerun()
        elif st.button("回答する"):
            if picked:
                sel = choice_map[picked]
                st.session_state.answers[idx] = sel
                st.session_state[feedback_key] = True
                st.rerun()
            else:
                st.warning("選択肢を選んでから回答してください。")
    else:
        sel = st.session_state.answers[idx]
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
            for k in list(st.session_state.keys()):
                if k.startswith("picked_") or k.startswith("feedback_shown_"):
                    del st.session_state[k]
            st.rerun()
# ==== 結果ページ ====
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
            if k != "authenticated":
                del st.session_state[k]
        st.rerun()
