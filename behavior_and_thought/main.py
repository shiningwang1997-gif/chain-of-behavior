# main.py
import argparse
from typing import List
from tasks.game24_extract import extract_expression_from_txt, validate_expression
import os

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["cot", "wf", "wf_execute"], required=True)
args = parser.parse_args()

numbers: List[int] = [1, 8, 10, 11]
os.makedirs("outputs", exist_ok=True)  # 确保 outputs 文件夹存在

def save_expression_with_validation(expr: str, numbers: List[int], path: str):
    is_valid = validate_expression(expr, numbers)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{expr}\n{is_valid}")
    print(f"表达式及验证结果已保存到：{path}")
    print(f"表达式：{expr}")
    print(f"验证结果：{is_valid}")

if args.mode == "cot":
    from tasks.game24_cot import solve_game24_cot
    # 生成结果
    result = solve_game24_cot(numbers)
    cot_txt_path = "outputs/game24_cot_result.txt"
    with open(cot_txt_path, "w", encoding="utf-8") as f:
        f.write(result)
    print("CoT 结果已保存到：", cot_txt_path)

    # 提取表达式并验证
    expr = extract_expression_from_txt(cot_txt_path)
    expr_txt_path = "outputs/game24_cot_expression.txt"
    save_expression_with_validation(expr, numbers, expr_txt_path)

elif args.mode == "wf":
    from tasks.game24_workflow import generate_game24_workflow_template
    # 生成工作流模板，只保存模板，不生成表达式文件
    workflow_txt = generate_game24_workflow_template(save=True)
    workflow_txt_path = "outputs/game24_workflow_template.txt"
    with open(workflow_txt_path, "w", encoding="utf-8") as f:
        f.write(workflow_txt)
    print("WF 工作流结果已保存到：", workflow_txt_path)

elif args.mode == "wf_execute":
    from tasks.game24_execute import execute_game24_workflow
    workflow_txt_path = "outputs/game24_workflow_template.txt"
    with open(workflow_txt_path, "r", encoding="utf-8") as f:
        workflow_txt = f.read()

    result = execute_game24_workflow(numbers, workflow_txt)
    execute_txt_path = "outputs/game24_execute_result.txt"
    with open(execute_txt_path, "w", encoding="utf-8") as f:
        f.write(result)
    print("WF 执行结果已保存到：", execute_txt_path)

    # 提取表达式并验证
    expr = extract_expression_from_txt(execute_txt_path)
    expr_txt_path = "outputs/game24_execute_expression.txt"
    save_expression_with_validation(expr, numbers, expr_txt_path)

# # main_test_extract.py
# from pathlib import Path
# from tasks.game24_extract import extract_expression_from_txt, validate_expression

# # 你现有的 outputs/game24_execute_result.txt
# txt_path = Path("outputs/game24_execute_result.txt")

# # 测试：提取表达式
# expr = extract_expression_from_txt(txt_path)
# print(f"提取的表达式: {expr}")

# # 如果你知道对应的数字，可以验证
# numbers_list = [
#     [4, 7, 2, 1],  # 举例：根据你真实的 Puzzles 填写
#     # 如果有多行，可以循环列表
# ]

# for numbers in numbers_list:
#     valid = validate_expression(expr, numbers)
#     print(f"对应数字 {numbers} 验证结果: {valid}")
