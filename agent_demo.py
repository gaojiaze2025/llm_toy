import json
import re
import os
import requests
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. 定义工具 (Tools)
def add_numbers(a: float, b: float) -> float:
    """对两个数字做加法运算"""
    return a + b

# 2. 工具注册表 (Tool Registry)
AVAILABLE_TOOLS = {
    "add_numbers": add_numbers,
}

# DeepSeek API 配置
DEEPSEEK_CONFIG = {
    "api_key": os.getenv("DEEPSEEK_API_KEY"),
    "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    "temperature": 0.1,
    "max_tokens": 2000
}

# 3. 真实的 DeepSeek API 调用函数（带重试逻辑）
def call_llm(history: list, system_prompt: str, max_retries: int = 3) -> str:
    """调用 DeepSeek API 并返回响应文本"""
    
    # 检查 API 密钥
    if not DEEPSEEK_CONFIG["api_key"]:
        raise ValueError("DeepSeek API key not found. Please set DEEPSEEK_API_KEY environment variable.")
    
    # 准备 API 请求数据
    messages = []
    
    # 添加系统提示词
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 添加历史对话记录
    for msg in history[1:]:  # 跳过第一个系统消息，因为我们已经单独添加了
        if msg["role"] in ["user", "assistant", "system"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        elif msg["role"] == "tool":
            # 将工具响应转换为用户消息格式，以便模型理解
            messages.append({"role": "user", "content": msg["content"]})
    
    # API 请求参数
    payload = {
        "model": DEEPSEEK_CONFIG["model"],
        "messages": messages,
        "temperature": DEEPSEEK_CONFIG["temperature"],
        "max_tokens": DEEPSEEK_CONFIG["max_tokens"],
        "stream": False
    }
    
    # API 请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_CONFIG['api_key']}"
    }
    
    # 重试逻辑
    for attempt in range(max_retries):
        try:
            # 发送 API 请求
            response = requests.post(
                f"{DEEPSEEK_CONFIG['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应数据
            result = response.json()
            llm_response = result["choices"][0]["message"]["content"]
            
            return llm_response.strip()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
            print(f"❌ {error_msg}")
            
            if attempt == max_retries - 1:  # 最后一次尝试失败
                return f"Error: {error_msg}"
            
            # 等待一段时间后重试（指数退避）
            wait_time = 2 ** attempt
            print(f"⏳ Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
        except (KeyError, IndexError) as e:
            error_msg = f"Failed to parse API response: {str(e)}"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"
    
    return "Error: Maximum retry attempts exceeded."

# 4. Agent 主循环函数
def run_agent_loop(initial_user_prompt: str, system_prompt: str, max_steps=5) -> str:
    
    # 历史记录初始化：只有 System Prompt 和用户指令
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_user_prompt}
    ]
    
    # 开始 Agent Loop
    for step in range(max_steps):
        print(f"\n--- 🔄 Step {step + 1} ---")
        
        # 4a. 感知与思考 (Perception & Thinking)
        llm_response = call_llm(history, system_prompt)
        print(f"LLM Response:\n{llm_response}")
        
        # 4b. 检查 Final Answer 标签 (判断终结)
        if "Final Answer:" in llm_response:
            final_answer = llm_response.split("Final Answer:", 1)[1].strip()
            return f"\n✅ Agent Finished! Final Answer: {final_answer}"
        
        # 4c. 检查 Action (判断工具调用)
        # 使用正则表达式来提取被 [ACTION_START] 和 [ACTION_END] 包裹的 JSON
        action_match = re.search(r"\[ACTION_START\]\s*(\{.*?\})\s*\[ACTION_END\]", llm_response, re.DOTALL)
        
        if action_match:
            # 找到 Action，将其添加到历史记录中
            action_json_str = action_match.group(1)
            history.append({"role": "assistant", "content": llm_response})
            
            # 4d. 解析 Action 并执行工具 (Action & Execution)
            try:
                action_dict = json.loads(action_json_str)
                tool_name = action_dict["tool"]
                tool_args = action_dict["args"]
                
                print(f"🛠️ Executing Tool: {tool_name} with args: {tool_args}")
                
                # 动态调用函数
                if tool_name not in AVAILABLE_TOOLS:
                    raise ValueError(f"Tool {tool_name} not registered.")
                
                tool_function = AVAILABLE_TOOLS[tool_name]
                observation_result = tool_function(**tool_args)
                
                # 4e. 格式化 Observation (新的感知)
                observation_message = f"Observation: {observation_result}"
                
                # 4f. 更新历史记录 (闭环)
                print(f"📢 Observation: {observation_result}")
                history.append({
                    "role": "tool", 
                    "content": observation_message
                })
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # 错误处理：如果 LLM 输出的 JSON 有误，将错误作为 Observation 返回
                error_message = f"Tool Execution Error: {e}"
                print(f"❌ {error_message}")
                history.append({"role": "tool", "content": f"Observation: {error_message}"})
        
        else:
            # LLM 没有给出 Final Answer 也没有给出 Action，视为错误或中间文本
            print("🛑 Error: LLM output is ambiguous. Stopping.")
            return "❌ Agent failed to produce a valid action or final answer."

    return "❌ Max steps reached without a final answer."

# --- 运行示例 ---

SYSTEM_PROMPT = """
你是智能计算器Agent。你的目标是根据用户指令完成数学计算。
你必须遵循 ReAct 框架：

## 输出格式要求：
1. **思考 (Thought)**: 描述你的推理过程、计划和要使用的工具。
2. **行动 (Action)**: 如果需要工具，必须输出 JSON 格式，并严格封装在 [ACTION_START] 和 [ACTION_END] 标签内。
3. **观察 (Observation)**: 这是工具返回的结果，你必须在下一轮 Thought 中利用它。

## 重要规则：
- 当你确定任务已完成时，必须以 'Final Answer:' 开头给出最终结果。
- 每次响应必须包含 Thought 部分
- 如果需要使用工具，必须严格按照 JSON 格式输出 Action
- 不要在一个响应中同时包含 Action 和 Final Answer

## 可用工具：
- {"tool": "add_numbers", "description": "对两个数字做加法运算", "args": {"a": float, "b": float}}

## 示例响应格式：
```
Thought: 我需要计算两个数字的和，我将使用 add_numbers 工具。
[ACTION_START]
{"tool": "add_numbers", "args": {"a": 123, "b": 456}}
[ACTION_END]
```

或

```
Thought: 我已经获得了计算结果，现在可以给出最终答案。
Final Answer: 123 加上 456 的结果是 579。
```
"""

user_input = "计算 123 加上 456 减去 789 的结果是多少？"
final_result = run_agent_loop(user_input, SYSTEM_PROMPT)
print(final_result)