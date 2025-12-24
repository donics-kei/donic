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
IMAGES_DIRNAME = "images"  # app.pyと同階層に置く（ローカル画像用）


# =========================
# ユーティリティ
# =========================
def safe_str(x) -> str:
    """None/NaN対策 + 前後空白除去"""
    if x is None:
        return ""
    s = str(x)
    if s.lower() in ("nan", "none"):
        return ""
    return s.strip()


def is_http_url(s: str) -> bool:
    try:
        u = urlparse(s)
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False


def normalize_answer_letter(x: str) -> str:
    """CSVの answer を a-e / A-E どちらでも受け取れるように統一"""
    s = safe_str(x).lower()
    return s if s in ["a", "b", "c", "d", "e"] else s


def auto_math_to_latex(text: str) -> str:
    """
    文字列中の表記を「表示用」に変換して返す。
    - 分数： 1/2 -> $\\frac{1}{2}$（縦分数）
    - ルート： √2, √(a+b), ルート3, sqrt(5) -> $\\sqrt{...}$
    ※CSVに "1/3" と入れていれば、pandasが数値化しない限り 0.333... にはなりません
    """
    if not text:
        return ""

    s = str(text)

    # すでに数式/LaTeXなら触らない（安全側）
    if "$" in s or "\\frac" in s or "\\sqrt" in s:
        return s

    # --- ルート変換（先） ---
    s = re.sub(r'\bsqrt\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'ルート\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'ルート\s*([0-9A-Za-z]+)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'√\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'√\s*([0-9A-Za-z]+)', r'$\\sqrt{\1}$', s)

    # --- 分数変換（最後） ---
    # 数字/数字 のときだけ縦分数へ（誤変換を避ける）
    s = re.sub(
        r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)',
        lambda m: f'$\\frac{{{m.group(1)}}}{{{m.group(2)}}}$',
        s
    )

    return s


def render_question_image(q: pd.Series) -> None:
    """image_url優先→なければimages/配下のファイルを表示"""
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


def render_choices_markdown(q: pd.Series) -> None:
    """選択肢をMarkdownで表示（radioにはA〜Eだけ出すので表示崩れなし）"""
    labels_upper = ["A", "B", "C", "D", "E"]
    for i in range(5):
        raw = safe_str(q.get(f"choice{i+1}", ""))
        st.markdown(f"**{labels_upper[i]}.** {auto_math_to_latex(raw)}")


# =========================
# データ読込（★重要：dtype=strで数値化を防ぐ）
# =========================
@st.cache_data
def load_questions() -> pd.DataFrame:
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, CSV_FILENAME)

    # ★ここが核心：全列を文字列で読み、"1/3"が0.333...にならないようにする
    df = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding="utf-8"
    )

    df.columns = df.columns.str.strip().str.lower()

    required = ["category", "question", "answer",
                "choice1", "choice2", "choice3", "choice4", "choice5"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSVに必須列がありません: {missing}")

    # 任意列が無ければ作る
    for c in ["image", "image_url", "explanation"]:
        if c not in df.columns:
            df[c] = ""

    # 前後空白除去
    for c in required + ["image", "image_url", "explanation"]:
        df[c] = df[c].astype(str).str.strip()

    # question空欄は除去
    df = df[df["question"] != ""]
    return df


# =========================
# セッション初期化
# =========================
defaults = {
    "page": "select",         # select / quiz / result
    "q_index": 0,
    "stage": "quiz",          # quiz / explanation（その都度採点時のみ）
    "answers": [],
    "start_times": [],
    "questions": None,
    "category": None,
    "num_questions": 20,
    "mode": "その都度採点",   # その都度採点 / 最後にまとめて採点
    "time_limit": DEFAULT_TIME_LIMIT,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================
# クイズ処理
# =========================
def render_quiz():
    idx = st.session_state.q_index
    q = st.session_state.questions.iloc[idx]

    st.markdown(f"### {auto_math_to_latex(safe_str(q.get('question','')))}")
    render_question_image(q)
    render_choices_markdown(q)

    # 回答選択はA〜Eのみ（数式をradioに入れない）
    picked = st.radio(
        "回答を選んでください：",
        ["A", "B", "C", "D", "E"],
        key=f"pick_{idx}",
        index=None,
        horizontal=True
    )

    # タイマー開始
    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    time_limit = int(st.session_state.time_limit)
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
        st.rerun()

    if st.button("回答する"):
        if picked:
            st.session_state.answers[idx] = picked.lower()  # a-e
            if st.session_state.mode == "その都度採点":
                st.session_state.stage = "explanation"
            else:
                st.session_state.q_index += 1
            st.rerun()
        else:
            st.warning("A〜Eのいずれかを選んでください。")

    # 既存仕様：毎秒更新（同時接続が多い場合は後で軽量化推奨）
    time.sleep(1)
    st.rerun()


def render_explanation():
    idx = st.session_state.q_index
    q = st.session_state.questions.iloc[idx]

    user = st.session_state.answers[idx]  # a-e or None
    correct = normalize_answer_letter(q.get("answer", ""))  # a-e

    labels = ["a", "b", "c", "d", "e"]
    labels_upper = ["A", "B", "C", "D", "E"]

    if user == correct:
        st.success("✅ 正解！")
    elif user is None:
        st.error("⏱ 未回答")
    else:
        st.error("❌ 不正解")

    # 正解表示
    if correct in labels:
        ci = labels.index(correct)
        st.markdown(f"**正解：{labels_upper[ci]}**  {auto_math_to_latex(safe_str(q.get(f'choice{ci+1}','')))}")
    else:
        st.markdown("**正解：不明（CSVの answer を確認してください）**")

    # 自分の回答表示
    if user in labels:
        ui = labels.index(user)
        st.markdown(f"あなたの回答：**{labels_upper[ui]}**  {auto_math_to_latex(safe_str(q.get(f'choice{ui+1}','')))}")
    else:
        st.markdown("あなたの回答：**未回答**")

    exp = auto_math_to_latex(safe_str(q.get("explanation", "")))
    if exp:
        st.info(f"📘 解説：{exp}")

    if st.button("次の問題へ"):
        st.session_state.q_index += 1
        st.session_state.stage = "quiz"
        st.rerun()


def render_result():
    st.title("📊 結果発表")

    labels = ["a", "b", "c", "d", "e"]
    labels_upper = ["A", "B", "C", "D", "E"]

    score = 0
    for i, q in st.session_state.questions.iterrows():
        user = st.session_state.answers[i]
        correct = normalize_answer_letter(q.get("answer", ""))

        ok = (user == correct)
        st.markdown(f"### Q{i+1} {'✅' if ok else '❌'}")
        st.markdown(f"**{auto_math_to_latex(safe_str(q.get('question','')))}**")

        render_question_image(q)
        render_choices_markdown(q)

        if user in labels:
            ui = labels.index(user)
            st.markdown(f"- あなたの回答：**{labels_upper[ui]}**  {auto_math_to_latex(safe_str(q.get(f'choice{ui+1}','')))}")
        else:
            st.markdown("- あなたの回答：**未回答**")

        if correct in labels:
            ci = labels.index(correct)
            st.markdown(f"- 正解：**{labels_upper[ci]}**  {auto_math_to_latex(safe_str(q.get(f'choice{ci+1}','')))}")
        else:
            st.markdown("- 正解：**不明**（CSVの answer を確認）")

        exp = auto_math_to_latex(safe_str(q.get("explanation", "")))
        if exp:
            st.markdown(f"📘 解説：{exp}")

        st.markdown("---")

        if ok:
            score += 1

    st.success(f"🎯 スコア：{score} / {st.session_state.num_questions}")

    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# =========================
# 画面：select
# =========================
if st.session_state.page == "select":
    st.title("SPI模擬試験（画像＋縦分数＋ルート対応）")

    try:
        df = load_questions()
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました: {e}")
        st.stop()

    categories = sorted(df["category"].unique().tolist())
    st.session_state.temp_category = st.radio("出題カテゴリー：", categories, index=0)
    st.session_state.temp_num_questions = st.number_input("出題数（1〜50）", 1, 50, value=20)
    st.session_state.temp_mode = st.radio("採点方法：", ["その都度採点", "最後にまとめて採点"])
    st.session_state.temp_time_limit = st.number_input("制限時間（1問あたり秒）", 5, 600, value=DEFAULT_TIME_LIMIT)

    st.caption(
        "【重要】CSVはdtype=strで読み込み、\"1/3\" が 0.333... に化けないようにしています。"
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


# =========================
# 画面：quiz
# =========================
if st.session_state.page == "quiz":
    if st.session_state.q_index >= int(st.session_state.num_questions):
        st.session_state.page = "result"
        st.rerun()

    st.title(f"Q{st.session_state.q_index + 1}/{st.session_state.num_questions}")

    if st.session_state.mode == "その都度採点" and st.session_state.stage == "explanation":
        render_explanation()
    else:
        render_quiz()

    st.stop()


# =========================
# 画面：result
# =========================
if st.session_state.page == "result":
    render_result()
    st.stop()
