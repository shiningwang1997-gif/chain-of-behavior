# tasks/game24_extract.py
import re
from pathlib import Path
from typing import Union, List
import ast
from collections import Counter

# ---------------------------
# 帮助函数：符号归一化 & 提取算术子串
# ---------------------------
def _normalize_symbols(s: str) -> str:
    """替换 LaTeX、Unicode 等符号为 Python 可识别的运算符号"""
    if not s:
        return s
    s = s.replace(r"\times", "*").replace(r"\div", "/")
    s = s.replace("×", "*").replace("÷", "/")
    s = s.replace("—", "-").replace("−", "-")
    # 去掉 Unicode 空白或不可见字符
    s = re.sub(r'[\u2000-\u200B\u00A0]', ' ', s)
    return s

def _extract_arith_substring(s: str) -> str:
    """
    从字符串 s 中提取最可能的算术表达式子串（只含数字、运算符、括号、小数点和空格）。
    """
    if not s:
        return ""

    s = s.strip()
    # 去掉尾部 =24 或 = 24
    s = re.sub(r'\s*=\s*24\s*$', '', s)
    # 去掉 LaTeX 括号 \(...\) \[...\]
    s = re.sub(r'\\[()\[\]]', '', s)
    # 去掉前后的星号、花括号、引号等常见 Markdown/格式残留
    s = s.strip(" *{}_`")
    # 若还有 '=', 取左侧
    if "=" in s:
        s = s.split("=", 1)[0].strip()

    # 找到允许字符片段
    cand_matches = re.findall(r'[\(\)\d\.\s\+\-\*\/]+', s)
    candidates = [m.strip() for m in cand_matches if re.search(r'\d', m) and re.search(r'[\+\-\*\/]', m)]
    if candidates:
        best = max(candidates, key=len).strip()
        best = re.sub(r'\s+', ' ', best)
        return best

    # 回退：只保留数字、运算符、括号、小数点和空格
    filtered = re.sub(r'[^0-9\(\)\+\-\*\/\. ]+', '', s)
    filtered = re.sub(r'\s+', ' ', filtered).strip()
    if filtered and re.search(r'\d', filtered) and re.search(r'[\+\-\*\/]', filtered):
        return filtered

    return ""

# ---------------------------
# 提取表达式
# ---------------------------
def extract_expression_from_txt(txt_path: Union[str, Path]) -> str:
    txt_path = Path(txt_path)
    if not txt_path.exists():
        return "无解"

    content = txt_path.read_text(encoding="utf-8")
    expr_candidate = ""

    # 1) 优先匹配 Answer:
    m = re.search(r'Answer\s*[:：]\s*(.*)', content, re.IGNORECASE)
    if m:
        after = m.group(1)
        first_line = after.splitlines()[0].strip()
        expr_candidate = first_line

    # 2) fallback: ``` 或 ```text 块
    if not expr_candidate:
        code_block_match = re.search(r'```(?:text)?\s*(.*?)```', content, re.DOTALL)
        if code_block_match:
            for line in code_block_match.group(1).splitlines():
                line = line.strip().rstrip('`')
                if line:
                    expr_candidate = line
                    break

    # 3) 最后回退: 全文逐行找算术表达式
    if not expr_candidate:
        for line in content.splitlines():
            line = line.strip()
            if re.search(r'\d', line) and re.search(r'[\+\-\*\/]', line):
                expr_candidate = line
                break

    # 归一化符号
    expr_candidate = _normalize_symbols(expr_candidate)
    # 抽取算术子串
    extracted = _extract_arith_substring(expr_candidate)

    if not extracted:
        return "无解"

    # 去掉首尾残留标点、空格、emoji
    extracted = extracted.strip()
    extracted = re.sub(r'^[^\d\(]+|[^\d\)]*$', '', extracted)
    extracted = re.sub(r'\s+', ' ', extracted).strip()

    return f"{extracted} = 24"

def extract_expressions_from_files(*txt_paths: Union[str, Path]) -> List[str]:
    return [extract_expression_from_txt(p) for p in txt_paths]

# ---------------------------
# 验证表达式
# ---------------------------
def validate_expression(expr: str, numbers: List[int]) -> bool:
    if expr == "无解":
        return False

    expr_main = expr.split('=')[0].strip()
    expr_main = _normalize_symbols(expr_main)  # ✅ Unicode 也归一化

    expr_numbers_counter = Counter(map(int, re.findall(r'\d+', expr_main)))
    numbers_counter = Counter(numbers)
    if expr_numbers_counter != numbers_counter:
        return False

    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
        ast.USub, ast.UAdd
    )
    try:
        node = ast.parse(expr_main, mode='eval')
        for n in ast.walk(node):
            if not isinstance(n, allowed_nodes):
                return False
        result = eval(expr_main)
    except Exception:
        return False

    return abs(result - 24) < 1e-6
