import streamlit as st
import pandas as pd
import time
import os
import re
from urllib.parse import urlparse
from fractions import Fraction
import math

# =========================
# 設定
# =========================
DEFAULT_TIME_LIMIT = 60
CSV_FILENAME = "spi_questions_converted.csv"
IMAGES_DIRNAME = "images"

# 小数→分数復元の上限（分母がこれ以下なら分数に戻す）
MAX_DENOMINATOR = 50


# =========================
# ユーティリティ
# =========================
def safe_str(x):
    """CSVの値を表示用文字列にする（Excel由来の0.3333…も救済）"""
    if x is None:
        return ""
    # pandas の NaN 対応
    try:
        if isinstance(x, float) and math.isnan(x):
            return ""
    except Exception:
        pass

    # Excelが1/3を0.3333…として保存したケースを復元
    if isinstance(x, (float, int)) and not isinstance(x, bool):
        # 整数はそのまま
        if float(x).is_integer():
            return str(int(x))

        # 0.3333333333 のような小数は分数へ（分母上限付き）
        frac = Fraction(float(x)).limit_denominator(MAX_DENOMINATOR)
        if frac.denominator != 1:
            return f"{frac.numerator}/{frac.denominator}"
        return str(x)

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
    s = safe_str(x).lower()
    return s if s in ["a", "b", "c", "d", "e"] else s


def auto_math_to_latex(text: str) -> str:
    """
    1/2  -> $\\frac{1}{2}$  (縦分数)
    √2   -> $\\sqrt{2}$
    """
    if not text:
        return ""

    s = str(text)

    # すでに数式/LaTeXなら触らない
    if "$" in s or "\\frac" in s or "\\sqrt" in s:
        return s

    # --- ルート ---
    s = re.sub(r'\bsqrt\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'ルート\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'ルート\s*([0-9A-Za-z]+)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'√\s*\(\s*([^)]+?)\s*\)', r'$\\sqrt{\1}$', s)
    s = re.sub(r'√\s*([0-9A-Za-z]+)', r'$\\sqrt{\1}$', s)

    # --- 分数（数字/数字のみ）---
    # ※ safe_str() が 0.3333… → "1/3" に戻してくれるので、ここで縦分数にできる
    s = re.sub(
        r'(?<!\d)(\d+)\s*/\s*(\d+)(?!\d)',
        lambda m: f'$\\frac{{{m.group(1)}}}{{{m.group(2)}}}$',
        s
    )

    return s


def render_question_image(q):
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

    # できるだけ文字として読む（Excelの自動型推論を避ける）
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    df.columns = df.columns.str.strip().str.lower()

    required = ["category", "question", "answer",
                "choice1", "choice2", "choice3", "choice4", "choice5"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSVに必須列がありません: {missing}")

    df["question"] = df["question"].astype(str).str.strip()
    df = df[df["question"] != ""]

    for col in ["image", "image_url", "explanation"]:
        if col not in df.columns:
            df[col] = ""

    df["category"] = df["category"].astype(str).str.strip()
    df["answer"] = df["answer"].astype(str).str.strip()

    return df


# =========================
# セッション初期化
# =========================
defaults = {
    "page": "select",
    "q_index": 0,
    "stage": "quiz",
    "answers": [],
    "start_times": [],
    "questions": None,
    "category": None,
    "num_questions": None,
    "mode": None,
    "time_limit": DEFAULT_TIME_LIMIT,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# =========================
# クイズ表示
# =========================
def render_quiz(q, idx, choices):
    question_text = auto_math_to_latex(safe_str(q.get("question", "")))
    st.markdown(f"### {question_text}")

    render_question_image(q)
    render_choices_markdown(choices)

    map_upper_to_lower = {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"}
    picked_upper = st.radio(
        "回答を選んでください：",
        ["A", "B", "C", "D", "E"],
        key=f"pick_{idx}",
        index=None,
        horizontal=True
    )

    if st.session_state.start_times[idx] is None:
        st.session_state.start_times[idx] = time.time()

    time_limit = int(st.session_state.get("time_limit", DEFAULT_TIME_LIMIT))
    remaining = max(0, int(time_limit - (time.time() - st.session_state.start_times[idx])))
    st.info(f"⏳ 残り時間：{remaining} 秒（制限 {time_limit} 秒）")

    if remaining <= 0:
        st.error("⌛ 時間切れ（未回答扱い）")
        st.session_state.answers[idx] = None
        if st.session_state.mode == "その都度採点":
            st.session_state.stage = "explanation"
        else:
            st.session_state.q_index += 1
        st.rerun()

    if st.button("回答する"):
        if picked_upper:
            st.session_state.answers[idx] = map_upper_to_lower[picked_upper]
            if st.session_state.mode == "その都度採点":
                st.session_state.stage = "explanation"
            else:
                st.session_state.q_index += 1
            st.rerun()
        else:
            st.warning("A〜Eのいずれかを選んでください。")

    # 既存仕様（毎秒更新）
    time.sleep(1)
    st.rerun()


def render_explanation(q, idx, choices):
    user = st.session_state.answers[idx]
    correct = normalize_answer_letter(q.get("answer", ""))

    labels = ["a", "b", "c", "d", "e"]
    labels_upper = ["A", "B", "C", "D", "E"]

    ci = labels.index(correct) if correct in labels else -1
    ui = labels.index(user) if user in labels else -1

    if user == correct:
        st.success("✅ 正解！")
    elif user is None:
        st.error("⏱ 未回答")
    else:
        st.error("❌ 不正解")

    if ci >= 0:
        st.markdown(f"**正解：{labels_upper[ci]}**  {auto_math_to_latex(safe_str(choices[ci]))}")
    else:
        st.markdown("**正解：不明（CSVの answer を確認してください）**")

    if ui >= 0:
        st.markdown(f"あなたの回答：**{labels_upper[ui]}**  {auto_math_to_latex(safe_str(choices[ui]))}")
    else:
        st.markdown("あなたの回答：**未回答**")

    exp = auto_math_to_latex(safe_str(q.get("explanation", "")))
    if exp:
        st.info(f"📘 解説：{exp}")

    if st.button("次の問題へ"):
        st.session_state.q_index += 1
        st.session_state.stage = "quiz"
        st.rerun()


def render_current_stage():
    idx = st.session_state.q_index
    q = st.session_state.questions.iloc[idx]
    choices = [q.get(f"choice{i+1}", "") for i in range(5)]

    if st.session_state.stage == "quiz":
        render_quiz(q, idx, choices)
    else:
        render_explanation(q, idx, choices)


# =========================
# 画面：開始
# =========================
if st.session_state.page == "select":
    st.title("SPI模擬試験（画像＋縦分数＋ルート対応）")

    df = load_questions()
    categories = sorted(df["category"].dropna().unique().tolist())

    st.session_state.temp_category = st.radio("出題カテゴリー：", categories, index=0)
    st.session_state.temp_num_questions = st.number_input("出題数（1〜50）", 1, 50, value=20)
    st.session_state.temp_mode = st.radio("採点方法：", ["その都度採点", "最後にまとめて採点"])
    st.session_state.temp_time_limit = st.number_input("制限時間（1問あたり秒）", 5, 600, value=DEFAULT_TIME_LIMIT)

    st.caption(
        "【重要】Excelで1/3を入れるとCSVに0.3333…で保存されがちです。\n"
        "このスクリプトは 0.3333… も分数に戻して縦分数表示します（分母上限50）。"
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
# 画面：本番
# =========================
if st.session_state.page == "quiz":
    if st.session_state.q_index >= int(st.session_state.num_questions):
        st.session_state.page = "result"
        st.rerun()

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

        st.markdown(f"### Q{i+1} {'✅' if user == correct else '❌'}")
        st.markdown(f"**{auto_math_to_latex(safe_str(q.get('question','')))}**")

        render_question_image(q)

        choices = [q.get(f"choice{j+1}", "") for j in range(5)]
        render_choices_markdown(choices)

        ui = labels.index(user) if user in labels else -1
        ci = labels.index(correct) if correct in labels else -1

        if ui >= 0:
            st.markdown(f"- あなたの回答：**{labels_upper[ui]}**  {auto_math_to_latex(safe_str(choices[ui]))}")
        else:
            st.markdown("- あなたの回答：**未回答**")

        if ci >= 0:
            st.markdown(f"- 正解：**{labels_upper[ci]}**  {auto_math_to_latex(safe_str(choices[ci]))}")
        else:
            st.markdown("- 正解：**不明**（CSVの answer を確認）")

        exp = auto_math_to_latex(safe_str(q.get("explanation", "")))
        if exp:
            st.markdown(f"📘 解説：{exp}")

        st.markdown("---")

        if user == correct:
            score += 1

    st.success(f"🎯 スコア：{score} / {st.session_state.num_questions}")

    if st.button("もう一度解く"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
