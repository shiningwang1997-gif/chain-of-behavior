from openai import OpenAI
import os

# 从环境变量里读取 API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 初始化客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

def call_llm_with_prompt(prompt: str, model: str = "deepseek-chat") -> str:
    """
    调用 DeepSeek 的 ChatCompletion API
    :param prompt: 用户输入的提示词（txt 内容）
    :param model: 模型名称，默认 deepseek-chat
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
