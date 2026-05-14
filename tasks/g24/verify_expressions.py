import os
import ast
import pandas as pd
import re

# --------------------------
# 配置路径
# --------------------------
RUN_CSV = "output/g24/run_expressions.csv"
STANDARD_CSV = "output/g24/standard_expressions.csv"

# --------------------------
# 工具函数
# --------------------------
def safe_eval(expr: str) -> float:
    """
    安全计算数学表达式，只允许数字、+-*/()运算。
    返回结果float，异常返回None
    """
    if not expr:
        return None
    try:
        # 替换常见中文或特殊符号为英文运算符
        expr_clean = expr.replace("−", "-").replace("×", "*").replace("÷", "/")
        # 移除其他非数字/运算符/括号字符
        expr_clean = re.sub(r"[^0-9+\-*/().]", "", expr_clean)
        # 防止数字后面直接跟括号，如 3(4+5) -> 3*(4+5)
        expr_clean = re.sub(r"(\d)\(", r"\1*(", expr_clean)
        return eval(expr_clean, {"__builtins__": None}, {})
    except Exception:
        return None

def digits_used_in_expr(expr: str) -> list:
    """
    从表达式中提取整数数字列表
    """
    numbers = re.findall(r"\d+", expr)
    return [int(n) for n in numbers]

def check_expression(input_numbers, expression) -> bool:
    """
    检查表达式是否等于24且只使用输入的数字各一次
    """
    if not expression or not input_numbers:
        return False

    # 1️⃣ 检查计算结果
    result = safe_eval(expression)
    if result is None or abs(result - 24) > 1e-6:
        return False

    # 2️⃣ 检查数字使用
    used_numbers = digits_used_in_expr(expression)
    return sorted(used_numbers) == sorted(input_numbers)

# --------------------------
# 验证单个 CSV
# --------------------------
def verify_single_csv(csv_path: str):
    if not os.path.exists(csv_path):
        print(f"⚠️ 文件不存在: {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    results = []
    for row in df.itertuples(index=False):
        # 解析 input
        try:
            input_numbers = ast.literal_eval(row.input)
        except Exception:
            input_numbers = []

        expression = row.expression
        is_valid = check_expression(input_numbers, expression)
        results.append({
            "input": row.input,
            "expression": expression,
            "valid": is_valid
        })

    result_df = pd.DataFrame(results)
    output_path = csv_path.replace(".csv", "_verify_results.csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"🎉 验证完成，结果已保存到 {output_path}")
    return output_path

# --------------------------
# CLI 主程序
# --------------------------
def main():
    print("🔍 验证 run_expressions.csv ...")
    verify_single_csv(RUN_CSV)
    print("🔍 验证 standard_expressions.csv ...")
    verify_single_csv(STANDARD_CSV)
    print("✅ 所有验证完成")

if __name__ == "__main__":
    main()
