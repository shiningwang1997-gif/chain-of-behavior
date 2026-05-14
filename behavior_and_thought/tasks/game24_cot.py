# tasks/game24_cot.py
from typing import List
from model.deepseek_client import call_llm_with_prompt
# from model.openrouter_client import call_llm_with_prompt
from prompts.prompt_templates import COT_24_TEMPLATE
import os

OUTPUT_DIR = "outputs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "game24_cot_result.txt")

def solve_game24_cot(numbers: List[int], save: bool = True) -> str:
    """用 CoT 提示词求解 24 点，并可保存结果到 TXT"""
    input_str = " ".join(map(str, numbers))
    prompt = COT_24_TEMPLATE.format(input=input_str)
    result = call_llm_with_prompt(prompt)

    if save:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(result)

    return result
