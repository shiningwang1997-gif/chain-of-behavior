import json
import os
import ast
import re
from copy import deepcopy
from prompts.sudoku.template import EXECUTE_WORKFLOW_TEMPLATE
from model.deepseek_client import call_llm_with_prompt

DATA_FILE = "data/sudoku/sudoku6x6_50.json"
OUTPUT_FILE = "output/sudoku/sudoku.jsonl"
STEP_TYPES = ["row", "column", "block"]

# ---------- Sudoku helpers ----------
def print_board(board):
    for row in board:
        print(" ".join(str(n) for n in row))
    print()

def has_zeros(board):
    return any(0 in row for row in board)

def parse_board_from_llm(result: str):
    cleaned = result.replace("Answer:", "").replace("```", "").replace("\\[", "").replace("\\]", "")
    matches = re.findall(r"\[\s*\d[\d,\s]*\]", cleaned, re.DOTALL)
    board = []
    for m in matches:
        try:
            row = ast.literal_eval(m)
            if isinstance(row, list):
                board.append(row)
        except:
            continue
    if len(board) == 6 and all(len(r) == 6 for r in board):
        return board
    try:
        return ast.literal_eval(cleaned)
    except:
        return None

# ---------- Step execution ----------
def execute_step(board, step_type):
    workflow_file = os.path.join("prompts", "sudoku", f"{step_type}.txt")
    with open(workflow_file, "r") as f:
        workflow_text = f.read()

    output_instruction = (
        "Answer: show all reasoning steps for this step.\n"
        "Include candidate placements, constraints, and merge decisions.\n"
        "⚠️ While filling cells, ensure that you do not repeat digits in any row, column, or 2×3 block.\n"
        "⚠️ IMPORTANT: You MUST NOT modify any cell that already contains a digit 1–6.\n"
        "   - Only cells that are exactly 0 are allowed to be filled.\n"
        "   - If a cell is non-zero, treat it as permanently fixed.\n"
        "Do NOT perform any external conflict checks or modify placements after output.\n"
        "Do NOT output the final board in any non-Python format.\n"
        "Use Python list format if you output a board."
    )

    prompt = EXECUTE_WORKFLOW_TEMPLATE.format(
        input=board,
        output=output_instruction,
        step_type=step_type,
        workflow=workflow_text
    )

    reasoning_result = call_llm_with_prompt(prompt)
    print(f"🧠 Step: {step_type} 推理过程：")
    print(reasoning_result)

    # ---------------- 二次提取提示词增强（已替换） ----------------
    extraction_prompt = (
        "Extract the proposed placements from the reasoning above in exact Python format: [[row_index, col_index, digit], ...].\n"
        "You must follow all rules below strictly:\n"
        "1. row_index and col_index must be 0-based.\n"
        "2. digit must be an integer from 1 to 6.\n"
        "3. You must not add or modify anything that is not explicitly stated in the reasoning.\n"
        "4. You must not modify any pre-filled non-zero digits in the original board, nor generate a digit for a cell that already contains a number.\n"
        "5. You must not invent new cells, coordinates, or digits.\n"
        "6. Do NOT include any text, markdown, explanations, comments, or extra symbols.\n"
        "7. Do NOT wrap the list in quotes.\n"
        "8. The output must be a valid Python list of lists parsable by ast.literal_eval().\n"
        "9. Any deviation from this format is considered an error.\n"
        "Example output:\n[[1,4,6],[2,3,5],...]\n\n"
        f"Reasoning steps:\n{reasoning_result}"
    )

    placements_str = call_llm_with_prompt(extraction_prompt)

    try:
        placements = ast.literal_eval(placements_str)
        if not isinstance(placements, list):
            placements = []
    except:
        placements = []

    board_next = deepcopy(board)
    for (r, c, d) in placements:
        if 0 <= r < 6 and 0 <= c < 6 and 1 <= d <= 6:
            board_next[r][c] = d

    print(f"\n🧩 Step: {step_type} 完成后的棋盘：")
    print_board(board_next)
    return board_next

# ---------- Input/Output ----------
def parse_indices_input(input_str):
    indices = set()
    parts = input_str.strip().split()
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            indices.update(range(int(start), int(end)+1))
        else:
            indices.add(int(part))
    return sorted(indices)

def load_existing_results():
    results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    results[obj["id"]] = obj["solved"]
    return results

def save_result(puzzle_id, board, existing_results):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    existing_results[puzzle_id] = board
    with open(OUTPUT_FILE, "w") as f:
        for pid, solved_board in existing_results.items():
            f.write(json.dumps({"id": pid, "solved": solved_board}, ensure_ascii=False) + "\n")

# ---------- Main ----------
def main():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    puzzles = data.get("puzzles", [])
    if not puzzles:
        print("⚠️ 没有 puzzle 数据")
        return

    existing_results = load_existing_results()
    user_input = input("请输入要运行的 puzzle 编号（支持 1, 1-40, 1-2 35 等）：")
    target_ids = parse_indices_input(user_input)

    for puzzle_data in puzzles:
        pid = puzzle_data["id"]
        if pid not in target_ids:
            continue

        board_current = puzzle_data["puzzle"]
        print(f"\n🚀 Solving sudoku id={pid}")
        print("Initial board:")
        print_board(board_current)

        step_idx = 0
        while has_zeros(board_current):
            step_type = STEP_TYPES[step_idx % 3]
            board_current = execute_step(board_current, step_type)
            step_idx += 1

        print("🎉 Sudoku solved! Final board:")
        print_board(board_current)
        save_result(pid, board_current, existing_results)

if __name__ == "__main__":
    main()
