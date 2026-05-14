# tasks/game24_execute.py
from typing import List
from model.deepseek_client import call_llm_with_prompt
# from model.openrouter_client import call_llm_with_prompt
from prompts.prompt_templates import EXECUTE_WORKFLOW_TEMPLATE
import os

OUTPUT_DIR = "outputs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "game24_execute_result.txt")

def execute_game24_workflow(numbers: List[int], workflow: str, save: bool = True) -> str:
    """
    根据 workflow 和具体数字执行 24 点任务，输出每一步计算过程，并可保存结果到 TXT
    """
    input_str = " ".join(map(str, numbers))
    prompt = EXECUTE_WORKFLOW_TEMPLATE.format(
        input=input_str,
        output="Answer: the final expression that uses each of these numbers exactly once "
            "and only the basic arithmetic operations + - * / ( ). "
            "Return the expression in the format: Answer: <expression> = 24",
        workflow=workflow
    )
    result = call_llm_with_prompt(prompt)

    if save:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(result)

    return result
