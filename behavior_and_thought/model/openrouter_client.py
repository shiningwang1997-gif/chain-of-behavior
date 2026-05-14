# model/openrouter_client.py
from openai import OpenAI
import os

# 从环境变量里读取 OpenRouter 的 API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# 初始化 OpenRouter 客户端（base_url 使用 openrouter 的 API 网关）
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def call_llm_with_prompt(prompt: str, model: str = "deepseek/deepseek-chat-v3.1:free") -> str:
    """
    调用 OpenRouter 上的 DeepSeek 模型（deepseek-chat-v3.1）。
    与 model/deepseek_client.py 的接口风格保持一致：接收 prompt 和可选 model 名称，返回文本。
    :param prompt: 用户输入的提示词（txt 内容）
    :param model: 模型名称，默认 deepseek/deepseek-chat-v3.1:free
    :return: 模型输出的文本
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    return response.choices[0].message.content