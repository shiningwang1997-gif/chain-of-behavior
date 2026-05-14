import os
import json
import pandas as pd
from typing import List

from model.deepseek_client import call_llm_with_prompt
from prompts.g24.template import STANDARD_TEMPLATE  # 使用 Python 模板

# --------------------------
# 输出文件夹
# --------------------------
OUTPUT_DIR = "output/g24"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------
# 构造 prompt（使用 STANDARD_TEMPLATE）
# --------------------------
def build_standard_prompt(numbers: List[int]) -> str:
    input_str = " ".join(map(str, numbers))
    return STANDARD_TEMPLATE.format(input=input_str)

# --------------------------
# 执行 prompt
# --------------------------
def execute_standard_for_numbers(numbers: List[int]) -> str:
    prompt = build_standard_prompt(numbers)
    response = call_llm_with_prompt(prompt)
    return response

# --------------------------
# 读取 CSV
# --------------------------
def read_csv(csv_path: str) -> List[List[int]]:
    df = pd.read_csv(csv_path)
    puzzles = []
    for _, row in df.iterrows():
        first_col = str(row[df.columns[0]])
        numbers = list(map(int, first_col.strip().split()))
        if len(numbers) != 4:
            raise ValueError(f"❌ Invalid line: {first_col}")
        puzzles.append(numbers)
    return puzzles

# --------------------------
# 处理单个 CSV
# --------------------------
def process_csv(csv_filename: str):
    number_str = os.path.splitext(csv_filename)[0]
    csv_path = os.path.join("data/g24", csv_filename)
    output_path = os.path.join(OUTPUT_DIR, f"{number_str}_standard.jsonl")

    print(f"\n🚀 Processing {csv_path} with STANDARD_TEMPLATE")

    puzzles = read_csv(csv_path)

    with open(output_path, "w", encoding="utf-8") as out:
        for i, numbers in enumerate(puzzles):
            try:
                llm_output = execute_standard_for_numbers(numbers)
                out.write(json.dumps({
                    "input": numbers,
                    "llm_output": llm_output
                }, ensure_ascii=False) + "\n")
                print(f"  ✅ Line {i+1} done")
            except Exception as e:
                print(f"  ❌ Line {i+1} error: {e}")

    print(f"🎉 Finished → saved to {output_path}")

# --------------------------
# 解析用户输入编号（支持范围、空格和逗号）
# --------------------------
def parse_numbers_input(nums_input: str) -> List[str]:
    result = []
    nums_input = nums_input.replace(" ", ",")
    parts = nums_input.split(",")
    for part in parts:
        if "-" in part:
            start, end = map(int, part.split("-"))
            result.extend([str(i) for i in range(start, end + 1)])
        elif part.isdigit():
            result.append(part)
    return result

# --------------------------
# 主函数
# --------------------------
def main():
    nums_input = input("请输入要处理的 24 点数据编号（例如 6 / 6 7 9 / 5-8 / 2,4-6,9）：").strip()
    numbers_list = parse_numbers_input(nums_input)

    for num in numbers_list:
        csv_path = os.path.join("data/g24", f"{num}.csv")
        if not os.path.exists(csv_path):
            print(f"❌ CSV 文件不存在：{csv_path}")
            continue
        process_csv(f"{num}.csv")

if __name__ == "__main__":
    main()
