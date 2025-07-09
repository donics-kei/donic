Python

import streamlit as st
import pandas as pd
import time
import os
import random

# Streamlitページの基本設定
st.set_page_config(page_title="SPI言語20問", layout="centered")

# カスタムCSSの適用
st.markdown("""
<style>
/* 全体のフォントを柔らかい印象に */
html, body, [class*="css"] {
    font-family: 'Hiragino Sans', 'ヒラギノ角ゴ ProN W3', 'メイリオ', Meiryo, sans-serif !important;
    font-size: 17px !important; /* 少し大きめにして読みやすく */
    color: #333333; /* やや濃いめのグレーで読みやすく */
}

/* ヘッダーの色をNICSの企業カラーに */
h1, h2, h3, h4, h5, h6 {
    color: #2196F3; /* NICSの企業カラー（水色） */
}

/* ボタンのスタイルをNICSカラーに */
div.stButton > button {
    background-color: #2196F3; /* 水色 */
    color: white;
    padding: 10px 24px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 8px; /* 角丸 */
    border: none;
    transition: background-color 0.3s ease; /* ホバー時のアニメーション */
}
div.stButton > button:hover {
    background-color: #0d47a1; /* 濃い目の水色 */
}

/* プログレスバーの色（タイマーにも使用） */
.stProgress > div > div > div > div {
    background-color: #2196F3; /* NICSの企業カラー（水色） */
}

/* 情報メッセージ（st.info）の背景色を調整 */
.stAlert > div {
    background-color: #e3f2fd; /* 水色の薄いバージョン */
    border-left: 8px solid #2196F3;
}

/* 成功メッセージ（st.success） */
.stSuccess > div {
    background-color: #e8f5e9;
    border-left: 8px solid #4CAF50;
}

/* 警告メッセージ（st.warning） */
.stWarning > div {
    background-color: #fff3e0;
    border-left: 8px solid #FF9800;
}

/* エラーメッセージ（st.error） */
.stError > div {
    background-color: #ffebee;
    border-left: 8px solid #F44336;
}

/* ラジオボタンのラベル */
.stRadio > label {
    font-size: 17px;
}

/* 問題文の強調 */
strong {
    color: #000000;
}

</style>
""", unsafe_allow_html=True)

# NICSロゴの表示（もしファイルが存在すれば）
if os.path.exists("nics_logo.png"):
    st.image("nics_logo.png", width=260)

# 質問データをキャッシュして高速化
@st.cache_data
def load_questions():
    # スクリプトのディレクトリからの相対パスでCSVを読み込む
    path = os.path.join(os.path.dirname(__file__), "spi_questions_converted.csv")
    if not os.path.exists(path):
        st.error("CSVファイルが見つかりません。スクリプトと同じディレクトリに 'spi_questions_converted.csv' を置いてください。")
        st.stop()
    df = pd.read_csv(path)
    # time_limitが空の場合は60秒を設定
    df["time_limit"] = df["time_limit"].fillna(60).astype(int)
    return df

# --- ログイン管理 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# メインコンテンツのプレースホルダーを定義
# これがスクリプト全体の描画を管理する
main_placeholder = st.empty()

# ログイン処理
if not st.session_state.authenticated:
    with main_placeholder.container(): # ログイン画面もこのコンテナで管理
        st.title("ログイン")
        username = st.text_input("ユーザーID", key="login_username")
        password = st.text_input("パスワード", type="password", key="login_password")
        if st.button("ログイン", key="login_button"):
            if username == "nics" and password == "nagasaki2025":
                st.session_state.authenticated = True
                main_placeholder.empty() # ログイン成功時にコンテナをクリア
                st.rerun()
            else:
                st.error("ユーザーIDまたはパスワードが違います。")
    st.stop() # ログインが完了するまでここで停止

# ログイン後、ページの初期化
if "page" not in st.session_state:
    st.session_state.page = "start"

# --- スタートページ ---
if st.session_state.page == "start":
    with main_placeholder.container(): # スタート画面もこのコンテナで管理
        st.title("SPI言語演習（20問ランダム）")
        st.markdown("""
        <ul style="list-style-type: disc; margin-left: 20px;">
            <li>制限時間があります</li>
            <li>回答後に解説が表示されます</li>
            <li>最後にスコアが表示されます</li>
        </ul>
        """, unsafe_allow_html=True)

        if st.button("演習スタート", key="start_quiz"):
            df = load_questions()
            # カテゴリが「言語」の問題のみを抽出
            filtered = df[df["category"].str.strip() == "言語"]
            if len(filtered) < 20:
                st.error("「言語」カテゴリの問題が20問未満です。CSVファイルを確認してください。")
                st.stop()
            # 20問をランダムに選択し、インデックスをリセット
            selected = filtered.sample(n=20).reset_index(drop=True)
            st.session_state.questions = selected
            st.session_state.answers = [None] * 20 # ユーザーの回答を格納
            st.session_state.q_index = 0 # 現在の問題インデックス
            st.session_state.start_times = [None] * 20 # 各問題の開始時刻を格納
            st.session_state.page = "quiz"
            
            # 🚀 ここが重要 🚀: 「演習スタート」ボタンのキーを削除
            if "start_quiz" in st.session_state:
                del st.session_state["start_quiz"] # これによりボタンの状態がリセットされる
            main_placeholder.empty() # コンテナをクリアして、前の要素を消す
            st.rerun()

# --- 出題・解説ページ ---
elif st.session_state.page == "quiz":
    with main_placeholder.container(): # クイズ画面もこのコンテナで管理
        idx = st.session_state.q_index # 現在の問題インデックス

        # 全20問が終わったら結果ページへ
        if idx >= 20:
            st.session_state.page = "result"
            main_placeholder.empty() # 結果ページへ遷移する前にもクリア
            st.rerun()

        q = st.session_state.questions.iloc[idx] # 現在の問題データ
        feedback_key = f"feedback_shown_{idx}" # 解説表示フラグ
        
        # 選択肢のラベルとテキストの準備
        labels = ["a", "b", "c", "d", "e"]
        choices = [q.get(f"choice{i+1}", "") for i in range(5)]
        # 空の選択肢を除外して表示用のリストを作成
        display_choices = [f"{l}. {c}" for l, c in zip(labels, choices) if c]
        choice_map = {f"{l}. {c}": l for l, c in zip(labels, choices) if c} # 表示テキストから内部ラベルへのマッピング

        # --- 解説フェーズ ---
        if st.session_state.get(feedback_key, False):
            st.header(f"Q{idx+1}/20")
            sel = st.session_state.answers[idx] # ユーザーの選択した回答
            correct_answer_label = str(q["answer"]).lower().strip() # 正解のラベル
            
            # 正解の選択肢テキストを取得
            correct_index = labels.index(correct_answer_label) if correct_answer_label in labels else -1
            correct_answer_text = choices[correct_index] if correct_index >= 0 else "不明"

            st.subheader("解答結果")
            if sel == correct_answer_label:
                st.success("🎉 正解！")
            else:
                st.error("❌ 不正解")
            
            st.markdown(f"**あなたの回答**: {'未回答' if sel is None else (sel.upper() + ' - ' + (choices[labels.index(sel)] if sel in labels else ''))}")
            st.markdown(f"**正解**: {correct_answer_label.upper()} - {correct_answer_text}")
            
            if q.get("explanation"):
                st.info(f"📘 解説：{q['explanation']}")
            
            st.markdown("---") # 区切り線
            if st.button("次へ", key=f"next_button_{idx}"):
                # 次のページへ進む前に、現在の問題のセッション状態（解説表示フラグとラジオボタン選択）をクリア
                for k in [f"picked_{idx}", f"feedback_shown_{idx}"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.session_state.q_index += 1 # 問題インデックスをインクリメント
                main_placeholder.empty() # コンテナをクリア
                st.rerun()

        # --- 出題フェーズ ---
        else:
            st.header(f"Q{idx+1}/20")
            st.markdown(f"**{q['question']}**") # 問題文の表示
            
            radio_key = f"picked_{idx}"
            # ユーザーが選択肢をすでに選んでいる場合はその値をセット (rerunで選択状態を維持するため)
            default_index = None
            if radio_key in st.session_state and st.session_state[radio_key] is not None:
                 try:
                     default_index = display_choices.index(st.session_state[radio_key])
                 except ValueError:
                     default_index = None # 見つからない場合はNoneに

            picked = st.radio("選択肢を選んでください：", display_choices, index=default_index, key=radio_key)

            # 問題開始時刻を記録（一度だけ）
            if st.session_state.start_times[idx] is None:
                st.session_state.start_times[idx] = time.time()

            elapsed_time = time.time() - st.session_state.start_times[idx]
            time_limit = int(q.get("time_limit", 60)) # CSVのtime_limitカラムを使用、デフォルト60秒
            
            remaining_time = max(0, int(time_limit - elapsed_time))

            # 残り時間をプログレスバーで表示
            progress_percentage = remaining_time / time_limit
            st.progress(progress_percentage, text=f"⏱ 残り時間：{remaining_time} 秒")

            # 時間切れの処理
            if remaining_time <= 0:
                st.warning("⌛ 時間切れ！未回答として次へ進みます。")
                st.session_state.answers[idx] = None # 未回答として記録
                st.session_state[feedback_key] = True # 解説フェーズへ移行
                main_placeholder.empty() # 時間切れ時もコンテナをクリア
                st.rerun()
            elif st.button("回答する", key=f"submit_button_{idx}"):
                if picked:
                    selected_label = choice_map[picked] # 選択されたテキストからラベルを取得
                    st.session_state.answers[idx] = selected_label # 回答を記録
                    st.session_state[feedback_key] = True # 解説フェーズへ移行
                    main_placeholder.empty() # 回答時もコンテナをクリア
                    st.rerun()
                else:
                    st.warning("選択肢を選んでください。")
            else:
                # 時間が経過したら自動で再描画してタイマーを更新
                time.sleep(1)
                st.rerun()

# --- 結果ページ ---
elif st.session_state.page == "result":
    with main_placeholder.container(): # 結果画面もこのコンテナで管理
        st.title("📊 結果発表")
        score = 0
        # 各問題の正誤を表示
        for i, q in st.session_state.questions.iterrows():
            your_answer_label = st.session_state.answers[i]
            correct_answer_label = str(q["answer"]).lower().strip()
            is_correct = (your_answer_label == correct_answer_label)
            
            labels = ["a", "b", "c", "d", "e"]
            choices = [q.get(f"choice{j+1}", "") for j in range(5)]

            # ユーザーの回答テキスト
            your_answer_text = "未回答"
            if your_answer_label in labels and labels.index(your_answer_label) < len(choices):
                your_answer_text = choices[labels.index(your_answer_label)]
            
            # 正解の回答テキスト
            correct_answer_text = "不明"
            if correct_answer_label in labels and labels.index(correct_answer_label) < len(choices):
                correct_answer_text = choices[labels.index(correct_answer_label)]
            
            st.markdown(f"**Q{i+1}: {q['question']}** {'✅ 正解' if is_correct else '❌ 不正解'}")
            st.markdown(f"あなたの回答：{your_answer_label.upper() if your_answer_label else '未回答'} - {your_answer_text}")
            st.markdown(f"正解：{correct_answer_label.upper()} - {correct_answer_text}")
            
            if q.get("explanation"):
                st.info(f"📘 解説：{q['explanation']}")
            st.markdown("---") # 区切り線
            
            if is_correct:
                score += 1
        
        st.success(f"🎯 最終スコア：{score}/20")

        if st.button("もう一度挑戦", key="retry_button"):
            # 認証状態以外全てのセッション状態をクリアしてリスタート
            for k in list(st.session_state.keys()):
                if k != "authenticated": # 認証状態は保持
                    del st.session_state[k]
            main_placeholder.empty() # コンテナをクリア
            st.rerun()
