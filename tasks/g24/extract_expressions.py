import os
import json
import re
import pandas as pd

OUTPUT_DIR = "output/g24"  # jsonl 文件目录
RUN_CSV = os.path.join(OUTPUT_DIR, "run_expressions.csv")
STANDARD_CSV = os.path.join(OUTPUT_DIR, "standard_expressions.csv")

# --------------------------
# 正则：只抓 Answer: ... = 24
# --------------------------
ANSWER_PATTERN = re.compile(r"Answer\s*[:：]\s*(.*?)\s*=\s*24", re.IGNORECASE)
ANSWER_PATTERN_DOTALL = re.compile(r"Answer\s*[:：]\s*(.*?)\s*=\s*24", re.IGNORECASE | re.DOTALL)
ANSWER_PATTERN_SIMPLE = re.compile(r"Answer\s*[:：]\s*(.*)", re.IGNORECASE)

# --------------------------
# 帮助函数：括号平衡检查
# --------------------------
def is_balanced(s: str) -> bool:
    """检查 () [] {} 三类括号是否都平衡（数量匹配）"""
    return s.count("(") == s.count(")") and s.count("[") == s.count("]") and s.count("{") == s.count("}")

# --------------------------
# 截断逻辑
# --------------------------
def truncate_after_first_expression(raw: str, max_lines: int = 6, max_chars: int = 400) -> str:
    if not raw:
        return ""

    # LaTeX display 优先
    m_display = re.search(r"\\\[(.*?)\\\]", raw, flags=re.DOTALL)
    if not m_display:
        m_display = re.search(r"\$\$(.*?)\$\$", raw, flags=re.DOTALL)
    if m_display:
        return m_display.group(1).strip()

    lines = raw.splitlines()
    acc = ""
    for i, ln in enumerate(lines[:max_lines]):
        fragment = ln.strip() if ln.strip() else " "
        acc = f"{acc} {fragment}" if acc else fragment
        if len(acc) > max_chars:
            break
        if is_balanced(acc):
            break

    candidate = acc.strip()
    if not is_balanced(candidate):
        candidate = " ".join(lines[:max_lines]).strip()

    delimiter_re = re.compile(
        r"\s*(?:—|--|-{2,}|;|\bcheck\b|\bCheck\b|\bLet’s\b|\bLet's\b|\bNote\b|: check|:Check).*",
        flags=re.DOTALL
    )
    if is_balanced(candidate):
        candidate = delimiter_re.split(candidate)[0].strip()

    return candidate[:max_chars].strip()

# --------------------------
# 清理末尾残留
# --------------------------
def clean_trailing_artifacts(expr: str) -> str:
    if not expr:
        return ""
    expr = re.sub(r"(\*\*|[+\-*/])+$", "", expr)
    expr = re.sub(r"\s+[A-Za-z].*$", "", expr)
    return expr.strip()

# --------------------------
# 安全替换 LaTeX 分数
# --------------------------
def replace_frac(expr: str) -> str:
    """
    将 LaTeX 分数 \frac{a}{b} 转换成 Python 表达式 (a) / (b)
    支持嵌套分数，保证括号完整
    """
    pattern = re.compile(r"\\frac\s*{([^{}]+)}{([^{}]+)}")
    while pattern.search(expr):
        expr = pattern.sub(r"(\1) / (\2)", expr)
    return expr

# --------------------------
# 清理表达式
# --------------------------
def clean_expr(expr: str) -> str:
    if not expr:
        return ""

    # 去掉 LaTeX 包裹
    expr = re.sub(r"\\\[(.*?)\\\]", r"\1", expr, flags=re.DOTALL)
    expr = re.sub(r"\$\$(.*?)\$\$", r"\1", expr, flags=re.DOTALL)
    expr = re.sub(r"\\\((.*?)\\\)", r"\1", expr, flags=re.DOTALL)
    expr = re.sub(r"(\\\[|\\\]|\\\(|\\\)|\$\$)", "", expr)

    expr = expr.replace("\n", " ")
    expr = re.sub(r"\s+", " ", expr).strip()
    expr = expr.lstrip("*` ")

    expr = expr.replace(r"\times", "*").replace(r"\div", "/").replace("×", "*").replace("÷", "/")
    expr = expr.replace(r"\left", "").replace(r"\right", "")

    expr = replace_frac(expr)
    expr = truncate_after_first_expression(expr)
    expr = clean_trailing_artifacts(expr)
    expr = re.sub(r"\s+", " ", expr).strip()
    return expr

# --------------------------
# 提取表达式
# --------------------------
def extract_expression(llm_output: str) -> str:
    if not llm_output:
        return ""

    # 倒序逐行查找 Answer
    lines = llm_output.splitlines()[::-1]
    for line in lines:
        match = ANSWER_PATTERN.search(line)
        if match:
            return clean_expr(match.group(1))

    match = ANSWER_PATTERN_DOTALL.search(llm_output)
    if match:
        return clean_expr(match.group(1))

    for line in lines:
        m2 = ANSWER_PATTERN_SIMPLE.search(line)
        if m2:
            return clean_expr(m2.group(1))

    m2 = ANSWER_PATTERN_SIMPLE.search(llm_output)
    if m2:
        return clean_expr(m2.group(1))

    return ""

# --------------------------
# 批处理 JSONL
# --------------------------
def process_jsonl_files(file_list, save_csv_path):
    all_rows = []
    for file_path in file_list:
        print(f"🔹 Processing {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception as e:
                    print(f"  ⚠️ 无法解析行（跳过）：{e}")
                    continue

                numbers = data.get("input", [])
                llm_output = data.get("llm_output", "")
                expression = extract_expression(llm_output)
                all_rows.append({
                    "input": numbers,
                    "expression": expression
                })

    df = pd.DataFrame(all_rows)
    df["input_str"] = df["input"].apply(lambda x: " ".join(map(str, x)) if isinstance(x, (list, tuple)) else str(x))
    df = df.sort_values("input_str").drop(columns=["input_str"])
    df.to_csv(save_csv_path, index=False, encoding="utf-8-sig")
    print(f"🎉 Saved CSV to {save_csv_path}")

# --------------------------
# 主程序
# --------------------------
def main():
    run_files = [
        os.path.join(OUTPUT_DIR, f)
        for f in os.listdir(OUTPUT_DIR)
        if f.endswith(".jsonl") and not f.endswith("_standard.jsonl")
    ]
    if run_files:
        process_jsonl_files(run_files, RUN_CSV)
    else:
        print("⚠️ 未找到 run.py 生成的 jsonl 文件")

    standard_files = [
        os.path.join(OUTPUT_DIR, f)
        for f in os.listdir(OUTPUT_DIR)
        if f.endswith("_standard.jsonl")
    ]
    if standard_files:
        process_jsonl_files(standard_files, STANDARD_CSV)
    else:
        print("⚠️ 未找到 run_standard.py 生成的 jsonl 文件")

if __name__ == "__main__":
    main()
