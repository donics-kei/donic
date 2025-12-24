import streamlit as st
import pandas as pd
import time
import os
import re
from urllib.parse import urlparse

# =========================
# 設定
# =========================
DEFAULT_TIME_LIMIT = 60
CSV_FILENAME = "spi_questions_converted.csv"
IMAGES_DIRNAME = "images"  # app.py と同じ階層に置く（ローカル画像用）


# =========================
# ユーティリティ
# =========================
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


def normalize_answer_letter(x: str) -> str:
    """CSVの answer を a-e / A-E どちらでも受け取れるように統一"""
    s = safe_str(x).lower()
    if s in ["a", "b", "c", "d", "e"]:
        return s
    return s


def auto_math_to_latex(text: str) -> str:
    """
    CSVに普通に書いた表記を、表示用に LaTeX（数式モード）へ自動変換。

    ✅ 分数： 1/2  ->  $\\frac{1}{2}$ （縦分数）
    ✅ ルート： √2, √(a+b), ルート3, sqrt(5) -> $\\sqrt{...}$

    ※ すでに $...$ や \\frac/\\sqrt が含まれている場合はそのまま（安全側）
    """
    if not text:
        return ""

    s = str(text)

    # すでに数式モード/LaTeXっぽいものがあるなら触らない
    if "$" in s or "\\frac" in s or "\\sqrt" in s:
        return s

    # --- ルート変換（先） ---
    # sqrt( ... ) -> $\sqrt{...}$
    s = re.sub(r'\bsqrt\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)

    # ルート( ... ) -> $\sqrt{...}$
    s = re.sub(r'ルート\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)

    # ルートX -> $\sqrt{X}$  (Xが数字/英字)
    s = re.sub(r'ルート\s*([0-9A-Za-z]+)', r'$\\sqrt{\1}$', s)

    # √( ... ) -> $\sqrt{...}$
    s = re.sub(r'√\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)

    # √X -> $\sqrt{X}$ (Xが数字/英字)
    s = re.sub(r'√\s*([0-9A-Za-z]+)', r'$\\sqrt{\1}$', s)

    # --- 分数変換（最後） ---
    # 1/2 -> $\frac{1}{2}$（数字/数字のみ対象）
    s = re.sub(
        r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)',
        lambda m: f'$\\frac{{{m.group(1)}}}{{{m.group(2)}}}$',
        s
    )

    return s


def render_question_image(q):
    """
    画像表示：
    1) image_url が http(s) のとき → それを表示
    2) image があるとき → images/<ファイル名> を表示
    """
    image_url = safe_str(q.get("image_url", ""))
    image_name = safe_str(q.get("image", ""))

    if image_url and is_http_url(image_url):
        st.image(image_url, use_container_width=True)
        return

    if image_name:
        base_dir = os.path.dirname(__file__)
        img_path = os.path.join(base_dir, IMAGES_DIRNAME, image_name)
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning(f"画像ファイルが見つかりません：{IMAGES_DIRNAME}/{image_name}")


def render_choices_markdown(choices):
    """選択肢を Markdown（LaTeX可）で表示（radioに数式を入れないため崩れない）"""
    labels_upper = ["A", "B", "C", "D", "E"]
    for i in range(5):
        c = auto_math_to_latex(safe_str(choices[i]))
        st.markdown(f"**{labels_upper[i]}.** {c}")


# =========================
# データ読込
# =========================
@st.cache_data
def load_questions():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, CSV_FILENAME)
    df = pd.read_csv(csv_path)

    df.columns = df.columns.str.strip().str.lower()

    required = ["category", "question", "answer",
                "choice1", "choice2", "choice3", "choice4", "choice5"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSVに必須列がありません: {missing}")

    df["question"] = df["question"].astype(str).str.strip()
    df = df[df["question"] != ""]

    # 任意列（なければ作る）
    if "image" not in df.columns:
        df["image"] = ""
    if "image_url" not in df.columns:
        df["image_url"] = ""
    if "explanation" not in df.columns:
        df["explanation"] = ""

    df["category"] = df["category"].astype(str).str.strip()
    df["answer"] = df["answer"].astype(str).str.strip()

    return df


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
# クイズ画面（選択肢はMarkdown表示＋回答はA〜E）
# =========================
def render_quiz(q, idx, choices):
    question_text = auto_math_to_latex(safe_str(q.get("question", "")))
    if question_text:
        st.markdown(f"### {question_text}")
    else:
        st.error("❗ 問題文が空欄です。")
        st.json(q.to_dict())
        st.stop()

    render_question_image(q)
    render_choices_markdown(choices)

    # 回答選択（A-Eのみ）
    map_upper_to_lower = {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}
    picked_upper = st.radio(
        "回答を選んでください：",
        ["A", "B", "C", "D", "E"],
        key=f"pick_{idx}",
        index=None,
        horizontal=True
    )

    # タイマー開始
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

        if st.session_state.mode == "その都度採点":
            st.session_state.stage = "explanation"
        else:
            st.session_state.q_index += 1
            st.session_state.stage = "quiz"
            del_key = f"pick_{idx}"
            if del_key in st.session_state:
                del st.session_state[del_key]

        st.rerun()
        st.stop()

    if st.button("回答する"):
        if picked_upper:
            st.session_state.answers[idx] = map_upper_to_lower[picked_upper]

            if st.session_state.mode == "その都度採点":
                st.session_state.stage = "explanation"
            else:
                st.session_state.q_index += 1
                st.session_state.stage = "quiz"
                del_key = f"pick_{idx}"
                if del_key in st.session_state:
                    del st.session_state[del_key]

            st.rerun()
            st.stop()
        else:
            st.warning("A〜Eのいずれかを選んでください。")
            st.stop()

    # 1秒ごと更新（同時接続が多い運用なら、後で軽量化版にするのがオススメ）
    time.sleep(1)
    st.rerun()
    st.stop()


def render_explanation(q, idx, choices):
    user = st.session_state.answers[idx]
    correct = normalize_answer_letter(q.get("answer", ""))

    labels = ["a", "b", "c", "d", "e"]
    labels_upper = ["A", "B", "C", "D", "E"]

    ci = labels.index(correct) if correct in labels else -1
    ui = labels.index(user) if user in labels else -1

    correct_txt = auto_math_to_latex(safe_str(choices[ci])) if ci >= 0 else "不明"
    user_txt = auto_math_to_latex(safe_str(choices[ui])) if ui >= 0 else "未回答"

    if user == correct:
        st.success("✅ 正解！")
    elif user is None:
        st.error("⏱ 未回答")
    else:
        st.error("❌ 不正解")

    if ci >= 0:
        st.markdown(f"**正解：{labels_upper[ci]}**  {correct_txt}")
    else:
        st.markdown("**正解：不明（CSVの answer を確認してください）**")

    if ui >= 0:
        st.markdown(f"あなたの回答：**{labels_upper[ui]}**  {user_txt}")
    else:
        st.markdown("あなたの回答：**未回答**")

    exp = auto_math_to_latex(safe_str(q.get("explanation", "")))
    if exp:
        st.info(f"📘 解説：{exp}")

    if st.button("次の問題へ"):
        st.session_state.q_index += 1
        st.session_state.stage = "quiz"
        del_key = f"pick_{idx}"
        if del_key in st.session_state:
            del st.session_state[del_key]
        st.rerun()
        st.stop()


def render_current_stage():
    idx = st.session_state.q_index
    q = st.session_state.questions.iloc[idx]
    choices = [safe_str(q.get(f"choice{i+1}", "")) for i in range(5)]

    if st.session_state.stage == "quiz":
        render_quiz(q, idx, choices)
    elif st.session_state.stage == "explanation":
        render_explanation(q, idx, choices)
    else:
        st.session_state.page = "select"
        st.rerun()
        st.stop()


# =========================
# 画面：開始
# =========================
if st.session_state.page == "select":
    st.title("NICS-SPI模擬試験")

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

    st.caption(
        "【分数】CSVに 1/2 と書けば縦分数で表示します（$\\frac{1}{2}$）。\n"
        "【ルート】CSVに √2 / √(a+b) / ルート3 / sqrt(5) と書けばルート表示します。\n"
        f"【画像】CSVに image（例 q001.png）を入れて {IMAGES_DIRNAME}/ に配置。URLなら image_url 列。"
    )

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
    labels = ["a", "b", "c", "d", "e"]
    labels_upper = ["A", "B", "C", "D", "E"]

    for i, q in st.session_state.questions.iterrows():
        user = st.session_state.answers[i]
        correct = normalize_answer_letter(q.get("answer", ""))

        correct_bool = (user == correct)

        st.markdown(f"### Q{i+1} {'✅' if correct_bool else '❌'}")
        st.markdown(f"**{auto_math_to_latex(safe_str(q.get('question','')))}**")

        render_question_image(q)

        choices = [safe_str(q.get(f"choice{j+1}", "")) for j in range(5)]
        render_choices_markdown(choices)

        ui = labels.index(user) if user in labels else -1
        ci = labels.index(correct) if correct in labels else -1

        user_txt = auto_math_to_latex(safe_str(choices[ui])) if ui >= 0 else "未回答"
        correct_txt = auto_math_to_latex(safe_str(choices[ci])) if ci >= 0 else "不明"

        st.markdown(f"- あなたの回答：**{labels_upper[ui]}**  {user_txt}" if ui >= 0 else "- あなたの回答：**未回答**")
        st.markdown(f"- 正解：**{labels_upper[ci]}**  {correct_txt}" if ci >= 0 else "- 正解：**不明**（CSVの answer を確認）")

        exp = auto_math_to_latex(safe_str(q.get("explanation", "")))
        if exp:
            st.markdown(f"📘 解説：{exp}")

        st.markdown("---")

        if correct_bool:
            score += 1

    st.success(f"🎯 スコア：{score} / {st.session_state.num_questions}")

    if st.button("もう一度解く"):
        keep_keys = ["authenticated"]
        for k in list(st.session_state.keys()):
            if k not in keep_keys:
                del st.session_state[k]
        st.rerun()
        st.stop()
