import json
import os
import ast
import re
from copy import deepcopy
from prompts.sudoku.template import STANDARD_TEMPLATE
from model.deepseek_client import call_llm_with_prompt

DATA_FILE = "data/sudoku/sudoku6x6_50.json"
OUTPUT_FILE = "output/sudoku/sudoku_standard.jsonl"

# ---------- Sudoku helpers ----------
def print_board(board):
    for row in board:
        print(" ".join(str(n) for n in row))
    print()

def parse_board_from_llm(result: str):
    """
    提取 LLM 输出的 6x6 棋盘，返回 [[6个数字],[6个数字],...]
    """
    cleaned = result.replace("Answer:", "").replace("```", "").replace("\\[", "").replace("\\]", "")
    # 尝试直接匹配行
    matches = re.findall(r"\[\s*\d[\d,\s]*\]", cleaned, re.DOTALL)
    board = []
    for m in matches:
        try:
            row = ast.literal_eval(m)
            if isinstance(row, list) and len(row) == 6:
                board.append(row)
        except:
            continue
    if len(board) == 6:
        return board
    # fallback 直接解析整个字符串
    try:
        b = ast.literal_eval(cleaned)
        if isinstance(b, list) and len(b) == 6 and all(len(r) == 6 for r in b):
            return b
    except:
        pass
    return None

# ---------- Standard step ----------
def execute_standard(board):
    output_instruction = (
        "Answer: Fill the entire 6x6 Sudoku board in Python list format.\n"
        "Return the board as a list of 6 lists, each containing exactly 6 integers.\n"
        "Each row, column, and 2x3 block must contain digits 1 through 6 exactly once.\n"
        "⚠️ While filling, ensure that no digit is repeated in any row, column, or 2×3 block.\n"
        "Do NOT perform any external conflict checks or modify placements after output.\n"
        "Return **only** the board as a list of lists."
    )

    prompt = STANDARD_TEMPLATE.format(
        input=board,
        output=output_instruction
    )

    reasoning_result = call_llm_with_prompt(prompt)
    print("🧠 Step: reasoning process:")
    print(reasoning_result)

    # 二次提取直接要求返回整行列表，不拆成 [r,c,d] （已替换为防乱填强化版）
    extraction_prompt = (
        "Extract the final 6x6 Sudoku board from the reasoning above in exact Python format.\n"
        "You must follow all rules below strictly:\n"
        "1. Return as a list of 6 lists, each containing exactly 6 integers.\n"
        "2. Each row, column, and 2x3 block must contain digits 1 through 6 exactly once.\n"
        "3. You must not add or modify anything that is not explicitly stated in the reasoning.\n"
        "4. You must not modify any pre-filled non-zero digits in the original board, nor generate a digit for a cell that already contains a number.\n"
        "5. You must not invent new cells, coordinates, or digits.\n"
        "6. Do NOT include any text, markdown, explanations, comments, or extra symbols.\n"
        "7. Do NOT wrap the list in quotes.\n"
        "8. The output must be a valid Python list of lists parsable by ast.literal_eval().\n"
        "9. Any deviation from this format is considered an error.\n"
        "Example output:\n[[5,3,6,1,2,4],[2,4,1,6,5,3],...]\n\n"
        f"Reasoning:\n{reasoning_result}"
    )
    board_result_str = call_llm_with_prompt(extraction_prompt)
    board_next = parse_board_from_llm(board_result_str)

    if board_next is None:
        board_next = deepcopy(board)
        print("⚠️ LLM 输出解析失败，保持原棋盘")

    print("\n🧩 Step: final board:")
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

        solved_board = execute_standard(board_current)

        print("🎉 Sudoku solved! Final board:")
        print_board(solved_board)
        save_result(pid, solved_board, existing_results)

if __name__ == "__main__":
    main()
