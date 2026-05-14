import os
import json

from model.deepseek_client import call_llm_with_prompt
from prompts.sliding.template import STANDARD_TEMPLATE

# --------------------------
# 路径配置
# --------------------------
DATA_FILE = "data/sliding/sliding.json"
OUTPUT_DIR = "output/sliding"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------
# 构造 prompt
# --------------------------
def build_standard_prompt(board):
    return STANDARD_TEMPLATE.format(input=board)

# --------------------------
# 执行单个 board
# --------------------------
def execute_standard(board):
    prompt = build_standard_prompt(board)
    response = call_llm_with_prompt(prompt)
    return response

# --------------------------
# 主逻辑
# --------------------------
def main():
    # 读取 sliding.json
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    boards = data.get("boards", [])
    if not boards:
        print("❌ sliding.json 中未找到 boards")
        return

    print(f"🚀 Loaded {len(boards)} sliding puzzles")

    for idx, board in enumerate(boards, start=1):
        print(f"🧩 Solving board {idx}")

        try:
            llm_output = execute_standard(board)

            output_path = os.path.join(OUTPUT_DIR, f"standard_{idx}.txt")
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(llm_output)

            print(f"  ✅ Saved to {output_path}")

        except Exception as e:
            print(f"  ❌ Error on board {idx}: {e}")

    print("🎉 All boards processed.")

if __name__ == "__main__":
    main()

