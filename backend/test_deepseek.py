"""DeepSeek API 连通性测试脚本

运行方式：
    cd backend
    python test_deepseek.py
"""
import asyncio
import sys

from app.core.config import get_settings
from app.services.deepseek_llm import DeepSeekLLM, DeepSeekMessage


async def test_chat():
    # 解决 Windows 终端 GBK 编码问题
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    settings = get_settings()
    print(f"Using model: {settings.DEEPSEEK_MODEL}")
    print(f"Base URL: {settings.DEEPSEEK_BASE_URL}")

    llm = DeepSeekLLM()
    messages = [
        DeepSeekMessage("system", "你是一位 Python 教学专家，回答简洁。"),
        DeepSeekMessage("user", "用一句话解释 Python 的 with 语句。"),
    ]

    print("\n--- 非流式调用 ---")
    response = await llm.achat(messages, temperature=0.7, max_tokens=512)
    print(response)

    print("\n--- 流式调用 ---")
    async for chunk in llm.achat_stream(messages, temperature=0.7, max_tokens=512):
        print(chunk, end="", flush=True)
    print()

    print("\n[OK] DeepSeek API 测试通过")


if __name__ == "__main__":
    asyncio.run(test_chat())
