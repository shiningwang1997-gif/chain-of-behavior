import pandas as pd
import argparse
import os
import tempfile
from pathlib import Path

from tasks.game24_extract import extract_expression_from_txt, validate_expression
from tasks.game24_cot import solve_game24_cot
from tasks.game24_execute import execute_game24_workflow

INPUT_CSV = "data/24.csv"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def batch_run(start_idx: int, end_idx: int, mode: str):
    df = pd.read_csv(INPUT_CSV)
    df_slice = df.iloc[start_idx-1:end_idx]  # 比如901-1000 -> df.iloc[900:1000]

    results = []

    for i, row in df_slice.iterrows():
        numbers = list(map(int, row['Puzzles'].split()))

        if mode == "cot":
            output_str = solve_game24_cot(numbers)   # LLM输出（字符串）
        elif mode == "wf_execute":
            workflow_txt_path = "outputs/game24_workflow_template.txt"
            with open(workflow_txt_path, "r", encoding="utf-8") as f:
                workflow_txt = f.read()
            output_str = execute_game24_workflow(numbers, workflow_txt)  # LLM输出（字符串）
        else:
            raise ValueError("mode must be 'cot' or 'wf_execute'")

        # --- 保存到临时文件 ---
        tmp_path = Path(tempfile.gettempdir()) / f"game24_out_{mode}_{i}.txt"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(output_str)

        # 提取表达式（传文件路径）
        expr = extract_expression_from_txt(tmp_path)
        # 验证
        valid = validate_expression(expr, numbers)

        # --- 保存结果，同时保存原始 LLM 输出 ---
        results.append({
            'num1': numbers[0],
            'num2': numbers[1],
            'num3': numbers[2],
            'num4': numbers[3],
            'raw_output': output_str,   # 这里保存完整 Step 1~N + Answer
            'expression': expr,
            'valid': valid
        })

    # 保存到 CSV
    output_csv = os.path.join(OUTPUT_DIR, f"batch_{mode}_{start_idx}_{end_idx}.csv")
    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"批量运行完成，结果已保存到 {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, choices=["cot", "wf_execute"])
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    args = parser.parse_args()

    batch_run(args.start, args.end, args.mode)
