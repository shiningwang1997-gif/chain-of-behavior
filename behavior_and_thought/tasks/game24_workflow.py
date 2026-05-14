# tasks/game24_workflow.py
import os
from model.deepseek_client import call_llm_with_prompt
# from model.openrouter_client import call_llm_with_prompt
from prompts.prompt_templates import WF_24_TEMPLATE

OUTPUT_DIR = "outputs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "game24_workflow_template.txt")

def generate_game24_workflow_template(save: bool = True) -> str:
    """
    生成一个通用的、可执行的 24 点工作流模板（纯文本格式）。
    如果 save=True，会保存到 outputs/game24_workflow_template.txt。
    返回 LLM 生成的 workflow 文本。
    """
    prompt = WF_24_TEMPLATE
    response = call_llm_with_prompt(prompt)

    # 保存到文件
    if save:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(response.strip())

    return response.strip()
