import streamlit as st
import pandas as pd
import time
import os
from urllib.parse import urlparse

# =========================
# 設定
# =========================
DEFAULT_TIME_LIMIT = 60  # 1問あたり秒数（開始画面で変更可）
CSV_FILENAME = "spi_questions_converted.csv"
IMAGES_DIRNAME = "image"  # 同梱画像フォルダ名

# =========================
# データ読込
# =========================
@st.cache_data
def load_questions():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, CSV_FILENAME)
    df = pd.read_csv(csv_path)

    # 列名を扱いやすく
    df.columns = df.columns.str.strip().str.lower()

    # 必須列チェック（最低限）
    required = ["category", "question", "answer", "choice1", "choice2", "choice3", "choice4", "choice5"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSVに必須列がありません: {missing}")

    # questionの空欄除去
    df["question"] = df["question"].astype(str).str.strip()
    df = df[df["question"] != ""]

    # 画像列（任意）
    # image: images/ 配下のファイル名（例 q001.png）
    # image_url: http(s):// の画像URL
    if "image" not in df.columns:
        df["image"] = ""
    if "image_url" not in df.columns:
        df["image_url"] = ""

    # explanation（任意）
    if "explanation" not in df.columns:
        df["explanation"] = ""

    # categoryを念のため文字列化
    df["category"] = df["category"].astype(str).str.strip()

    # answerを正規化
    df["answer"] = df["answer"].astype(str).str.strip().str.lower()

    return df


def safe_str(x):
    if x is None:
        return ""
    s = str(x).strip()
    if s.lower() in ["nan", "none"]:
        return ""
    return s


def is_http_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except:
        return False


def render_question_image(q):
    """
    画像表示：
    1) image_url が http(s) のとき → それを表示
    2) image があるとき → images/<ファイル名> を表示
    どちらも無いなら何もしない
    """
    image_url = safe_str(q.get("image_url", ""))
    image_name = safe_str(q.get("image", ""))

    # URL優先
    if image_url and is_http_url(image_url):
        st.image(image_url, use_container_width=True)
        return

    # 同梱ファイル
    if image_name:
        base_dir = os.path.dirname(__file__)
        img_path = os.path.join(base_dir, IMAGES_DIRNAME, image_name)
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning(f"画像ファイルが見つかりません：{IMAGES_DIRNAME}/{image_name}")


# =========================
# セッション初期化
# =========================
defaults = {
    "page": "select",
    "q_index": 0,
    "stage": "quiz",          # quiz / explanation
    "answers": [],
    "start_times": [],
    "questions": None,
    "category": None,
    "num_questions": None,
    "mode": None,             # その都度採点 / 最後にまとめて採点
    "time_limit": DEFAULT_TIME_LIMIT,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================
# セッション復元（リロード対策）
# =========================
if st.session_state.page != "select" and st.session_state.questions is None:
    try:
        df = load_questions()
        cat = st.session_state.get("category", "非言語")
        num = int(st.session_state.get("num_questions", 20))
        pool = df[df["category"] == cat]
        if len(pool) < num:
            st.session_state.page = "select"
            st.error(f"カテゴリ「{cat}」の問題数が不足しています（必要{num}問 / 現在{len(pool)}問）")
            st.stop()

        st.session_state.questions = pool.sample(n=num).reset_index(drop=True)
        st.session_state.answers = [None] * num
        st.session_state.start_times = [None] * num
        st.warning("⚠️ セッション切れのため問題を復元しました。")
    except Exception as e:
        st.session_state.page = "select"
        st.error(f"セッション復元に失敗しました: {e}")
        st.stop()


# =========================
# 画面：クイズ
# =========================
def render_quiz(q, idx, choices, labeled, labels):
    # 問題文
    question_text = safe_str(q.get("question", ""))
    if question_text:
        st.subheader(question_text)
    else:
        st.error("❗ 問題文が空欄です。")
        st.json(q.to_dict())
        st.stop()

    # 画像（あれば表示）
    render_question_image(q)

    # 選択肢
    picked = st.radio("選択肢を選んでください：", labeled, key=f"q{idx}", index=None)

    # タイマー
    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    time_limit = int(st.session_state.get("time_limit", DEFAULT_TIME_LIMIT))
    elapsed = time.time() - st.session_state.start_times[idx]
    remaining = max(0, int(time_limit - elapsed))

    st.info(f"⏳ 残り時間：{remaining} 秒（制限 {time_limit} 秒）")

    # 時間切れ
    if remaining <= 0:
        st.error("⌛ 時間切れ（未回答扱い）")
        st.session_state.answers[idx] = None

        # その都度採点モードなら解説へ
        if st.session_state.mode == "その都度採点":
            st.session_state.stage = "explanation"
            st.rerun()
            st.stop()
        else:
            # まとめ採点モードなら次へ
            st.session_state.q_index += 1
            st.session_state.stage = "quiz"
            del_key = f"q{idx}"
            if del_key in st.session_state:
                del st.session_state[del_key]
            st.rerun()
            st.stop()

    # 回答ボタン
    if st.button("回答する"):
        if picked:
            st.session_state.answers[idx] = labels[labeled.index(picked)]

            if st.session_state.mode == "その都度採点":
                st.session_state.stage = "explanation"
            else:
                # まとめ採点は即次へ
                st.session_state.q_index += 1
                st.session_state.stage = "quiz"
                del_key = f"q{idx}"
                if del_key in st.session_state:
                    del st.session_state[del_key]

            st.rerun()
            st.stop()
        else:
            st.warning("選択肢を選んでください。")
            st.stop()

    # 1秒ごとに更新（現行仕様を踏襲）
    time.sleep(1)
    st.rerun()
    st.stop()


def render_explanation(q, idx, choices, labels):
    user = st.session_state.answers[idx]
    correct = safe_str(q.get("answer", "")).lower()

    ci = labels.index(correct) if correct in labels else -1
    correct_txt = choices[ci] if ci >= 0 else "不明"

    ui = labels.index(user) if user in labels else -1
    user_txt = choices[ui] if ui >= 0 else "未回答"

    if user == correct:
        st.success("✅ 正解！")
    elif user is None:
        st.error("⏱ 未回答")
    else:
        st.error("❌ 不正解")

    st.markdown(f"**正解：{correct.upper()} - {correct_txt}**")
    st.markdown(f"あなたの回答：{user.upper() if user else '未回答'} - {user_txt}")

    exp = safe_str(q.get("explanation", ""))
    if exp:
        st.info(f"📘 解説：{exp}")

    if st.button("次の問題へ"):
        st.session_state.q_index += 1
        st.session_state.stage = "quiz"
        del_key = f"q{idx}"
        if del_key in st.session_state:
            del st.session_state[del_key]
        st.rerun()
        st.stop()


def render_current_stage():
    idx = st.session_state.q_index
    q = st.session_state.questions.iloc[idx]

    labels = ['a', 'b', 'c', 'd', 'e']
    choices = [safe_str(q.get(f"choice{i+1}", "")) for i in range(5)]
    labeled = [f"{l}. {c}" for l, c in zip(labels, choices)]

    if st.session_state.stage == "quiz":
        render_quiz(q, idx, choices, labeled, labels)
    elif st.session_state.stage == "explanation":
        render_explanation(q, idx, choices, labels)
    else:
        st.warning("❗ ステージ不明。select に戻ります")
        st.session_state.page = "select"
        st.rerun()
        st.stop()


# =========================
# 画面：開始
# =========================
if st.session_state.page == "select":
    st.title("SPI模擬試験")

    df = None
    try:
        df = load_questions()
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
        st.stop()

    categories = sorted(df["category"].dropna().unique().tolist())
    if not categories:
        st.error("CSVに category がありません。")
        st.stop()

    st.session_state.temp_category = st.radio("出題カテゴリー：", categories, index=0)

    st.session_state.temp_num_questions = st.number_input("出題数（1〜50）", 1, 50, value=20)

    st.session_state.temp_mode = st.radio("採点方法：", ["その都度採点", "最後にまとめて採点"])

    st.session_state.temp_time_limit = st.number_input("制限時間（1問あたり秒）", 5, 600, value=DEFAULT_TIME_LIMIT)

    st.caption(f"画像を使う場合：CSVに image 列（例 q001.png）を追加し、{IMAGES_DIRNAME}/ に画像を入れてください。URLなら image_url 列。")

    if st.button("開始"):
        cat = st.session_state.temp_category
        n = int(st.session_state.temp_num_questions)

        pool = df[df["category"] == cat]
        if len(pool) < n:
            st.error(f"カテゴリ「{cat}」の問題数が不足しています（必要{n}問 / 現在{len(pool)}問）")
            st.stop()

        st.session_state.category = cat
        st.session_state.num_questions = n
        st.session_state.mode = st.session_state.temp_mode
        st.session_state.time_limit = int(st.session_state.temp_time_limit)

        st.session_state.questions = pool.sample(n=n).reset_index(drop=True)
        st.session_state.answers = [None] * n
        st.session_state.start_times = [None] * n
        st.session_state.q_index = 0
        st.session_state.stage = "quiz"
        st.session_state.page = "quiz"

        st.rerun()
        st.stop()

    st.stop()


# =========================
# 画面：本番
# =========================
if st.session_state.page == "quiz":
    if st.session_state.q_index >= int(st.session_state.num_questions):
        st.session_state.page = "result"
        st.rerun()
        st.stop()

    st.title(f"Q{st.session_state.q_index + 1}/{st.session_state.num_questions}")
    render_current_stage()
    st.stop()


# =========================
# 画面：結果
# =========================
if st.session_state.page == "result":
    st.title("📊 結果発表")

    score = 0
    labels = ['a', 'b', 'c', 'd', 'e']

    for i, q in st.session_state.questions.iterrows():
        user = st.session_state.answers[i]
        correct = safe_str(q.get("answer", "")).lower()
        correct_bool = user == correct

        st.markdown(f"### Q{i+1} {'✅' if correct_bool else '❌'}")
        st.markdown(f"**{safe_str(q.get('question',''))}**")

        # 画像（あれば表示）
        render_question_image(q)

        choices = [safe_str(q.get(f"choice{j+1}", "")) for j in range(5)]

        user_txt = choices[labels.index(user)] if user in labels else "未回答"
        correct_txt = choices[labels.index(correct)] if correct in labels else "不明"

        st.markdown(f"- あなたの回答：{user.upper() if user else '未回答'} - {user_txt}")
        st.markdown(f"- 正解：{correct.upper() if correct else '不明'} - {correct_txt}")

        exp = safe_str(q.get("explanation", ""))
        if exp:
            st.markdown(f"📘 解説：{exp}")

        st.markdown("---")

        if correct_bool:
            score += 1

    st.success(f"🎯 スコア：{score} / {st.session_state.num_questions}")

    if st.button("もう一度解く"):
        keep_keys = ["authenticated"]  # もし何か認証を使っている場合だけ残す
        for k in list(st.session_state.keys()):
            if k not in keep_keys:
                del st.session_state[k]
        st.rerun()
        st.stop()

