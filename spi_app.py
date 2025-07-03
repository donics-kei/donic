import streamlit as st
import pandas as pd
import time
import os

st.set_page_config(page_title="SPI言語20問", layout="centered")

@st.cache_data
def load_questions():
    path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(path):
        st.error("CSVファイルが見つかりません。")
        st.stop()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    df["question"] = df["question"].astype(str).str.strip()
    df = df[df["question"] != ""]
    df["time_limit"] = df.get("time_limit", 60)
    return df

# === ログイン ===
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("ログイン")
    user = st.text_input("ユーザーID")
    pw = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if user == "nics" and pw == "nagasaki2025":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("ユーザーIDまたはパスワードが違います")
    st.stop()

# === 初期化 ===
if "page" not in st.session_state:
    st.session_state.page = "start"

# === スタート画面 ===
if st.session_state.page == "start":
    st.title("SPI言語演習（20問ランダム）")
    st.markdown("・制限時間あり\n・解答後に解説表示\n・スコア付き")
    if st.button("演習スタート"):
        df = load_questions()
        words = df[df["category"].str.strip() == "言語"]
        if len(words) < 20:
            st.error("「言語」カテゴリの問題が20問未満です")
            st.stop()
        st.session_state.questions = words.sample(n=20).reset_index(drop=True)
        st.session_state.answers = [None] * 20
        st.session_state.q_index = 0
        st.session_state.start_times = [None] * 20
        st.session_state.phase = "question"
        st.session_state.page = "quiz"
        st.rerun()

# === 出題／解説ページ ===
elif st.session_state.page == "quiz":
    idx = st.session_state.q_index
    if idx >= 20:
        st.session_state.page = "result"
        st.rerun()

    q = st.session_state.questions.iloc[idx]
    labels = ["a", "b", "c", "d", "e"]
    choices = [q.get(f"choice{i+1}", "") for i in range(5)]
    choice_map = {f"{l}. {c}": l for l, c in zip(labels, choices)}

    st.header(f"Q{idx+1}/20")
    st.markdown(f"**{q['question']}**")

    # === 解説フェーズ ===
    if st.session_state.phase == "feedback":
        sel = st.session_state.answers[idx]
        correct = str(q["answer"]).lower().strip()
        ci = labels.index(correct) if correct in labels else -1

        if sel == correct:
            st.success("正解！")
        elif sel is None:
            st.error("未回答")
        else:
            st.error("不正解")

        if ci >= 0:
            st.markdown(f"正解：{correct.upper()} - {choices[ci]}")
        if q.get("explanation"):
            st.info(f"📘 解説：{q['explanation']}")

        if st.button("次の問題へ"):
            st.session_state.q_index += 1
            st.session_state.phase = "question"
            st.rerun()
        return

    # === 出題フェーズ ===
    else:
        key = f"picked"
        picked = st.radio("選択肢を選んでください：", list(choice_map.keys()), index=None, key=key)

        if st.session_state.start_times[idx] is None:
            st.session_state.start_times[idx] = time.time()

        elapsed = time.time() - st.session_state.start_times[idx]
        limit = int(q.get("time_limit", 60))
        remaining = max(0, int(limit - elapsed))
        st.info(f"⏱ 残り時間：{remaining} 秒")

        if remaining <= 0:
            st.warning("⌛ 時間切れ")
            st.session_state.answers[idx] = None
            st.session_state.phase = "feedback"
            st.rerun()
            return

        if st.button("回答する"):
            if picked and picked in choice_map:
                st.session_state.answers[idx] = choice_map[picked]
                st.session_state.phase = "feedback"
                st.rerun()
                return
            else:
                st.warning("選択肢を選んでください")
                return

        time.sleep(1)
        st.rerun()
        return

# === 結果ページ ===
elif st.session_state.page == "result":
    st.title("📊 結果発表")
    score = 0
    labels = ["a", "b", "c", "d", "e"]
    for i, q in st.session_state.questions.iterrows():
        your = st.session_state.answers[i]
        ans = str(q["answer"]).lower().strip()
        correct = (your == ans)
        choices = [q.get(f"choice{j+1}", "") for j in range(5)]
        your_txt = choices[labels.index(your)] if your in labels else "未回答"
        ans_txt = choices[labels.index(ans)] if ans in labels else "不明"
        st.markdown(f"**Q{i+1}: {q['question']}** {'✅' if correct else '❌'}")
        st.markdown(f"あなたの回答：{your.upper() if your else '未回答'} - {your_txt}")
        st.markdown(f"正解：{ans.upper()} - {ans_txt}")
        if q.get("explanation"):
            st.markdown(f"📘 解説：{q['explanation']}")
        st.markdown("---")
        if correct:
            score += 1

    st.success(f"🎯 最終スコア：{score} / 20")

    if st.button("もう一度挑戦"):
        for k in list(st.session_state.keys()):
            if k not in ["authenticated"]:
                del st.session_state[k]
        st.rerun()
