import os
import json
import pandas as pd
from typing import List

from model.deepseek_client import call_llm_with_prompt
from prompts.g24.template import EXECUTE_WORKFLOW_TEMPLATE  # 使用 Python 模板

# --------------------------
#  输出文件夹
# --------------------------
OUTPUT_DIR = "output/g24"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------
#  加载 workflow 文件
# --------------------------
def load_workflow(number_str: str) -> str:
    workflow_path = os.path.join("prompts", "g24", f"{number_str}.txt")
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f"❌ Workflow file not found: {workflow_path}")
    with open(workflow_path, "r", encoding="utf-8") as f:
        return f.read()

# --------------------------
#  构造 prompt（仿照老项目）
# --------------------------
def build_prompt(numbers: List[int], workflow: str) -> str:
    input_str = " ".join(map(str, numbers))
    output_instruction = (
        "Answer: show all intermediate calculation steps (Step 1, Step 2, ...) "
        "and the final expression using each number exactly once with + - * / ( ). "
        "Return in format: Answer: <expression> = 24"
    )
    return EXECUTE_WORKFLOW_TEMPLATE.format(
        input=input_str,
        output=output_instruction,
        workflow=workflow
    )

# --------------------------
#  执行 workflow
# --------------------------
def execute_workflow_for_numbers(numbers: List[int], workflow: str) -> str:
    prompt = build_prompt(numbers, workflow)
    response = call_llm_with_prompt(prompt)
    return response

# --------------------------
#  读取 CSV
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
#  单个 CSV 文件处理
# --------------------------
def process_csv(csv_filename: str):
    number_str = os.path.splitext(csv_filename)[0]
    csv_path = os.path.join("data/g24", csv_filename)
    output_path = os.path.join(OUTPUT_DIR, f"{number_str}.jsonl")

    print(f"\n🚀 Processing {csv_path}")

    workflow = load_workflow(number_str)
    puzzles = read_csv(csv_path)

    with open(output_path, "w", encoding="utf-8") as out:
        for i, numbers in enumerate(puzzles):
            try:
                llm_output = execute_workflow_for_numbers(numbers, workflow)
                out.write(json.dumps({
                    "input": numbers,
                    "llm_output": llm_output
                }, ensure_ascii=False) + "\n")
                print(f"  ✅ Line {i+1} done")
            except Exception as e:
                print(f"  ❌ Line {i+1} error: {e}")

    print(f"🎉 Finished → saved to {output_path}")

# --------------------------
#  新增：解析用户输入编号
# --------------------------
def parse_numbers_input(user_input: str):
    """
    支持：
    - "6"
    - "6 7 9"
    - "6,7,9"
    - "5-8"
    - "2, 4-6, 9"
    返回：["6", "7", "9", ...]
    """
    items = user_input.replace(",", " ").split()
    result = []

    for item in items:
        if "-" in item:
            start, end = item.split("-")
            for x in range(int(start), int(end) + 1):
                result.append(str(x))
        else:
            result.append(item.strip())

    # 去重 & 排序
    result = sorted(set(result), key=lambda x: int(x))
    return result

# --------------------------
#  主函数：一次支持多个编号
# --------------------------
def main():
    print("请输入要处理的 24 点数据编号（例如：6 / 6 7 9 / 5-8 / 2,4-6,9）：")
    user_input = input("编号 = ").strip()

    numbers_list = parse_numbers_input(user_input)
    print(f"\n👉 将处理这些编号：{numbers_list}\n")

    for num in numbers_list:
        csv_path = os.path.join("data/g24", f"{num}.csv")
        if not os.path.exists(csv_path):
            print(f"⚠️ 跳过：CSV 文件不存在 → {csv_path}")
            continue

        process_csv(f"{num}.csv")

    print("\n✨ 全部处理完成！")

if __name__ == "__main__":
    main()
