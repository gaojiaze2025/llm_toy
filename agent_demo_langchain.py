"""
LangChain version of the ReAct agent demo.

This script replicates the functionality of `agent_demo.py` using the LangChain framework.
It defines a simple calculator agent with a single tool `add_numbers`, connects to the
DeepSeek API via ChatOpenAI, and runs a ReAct-style agent loop.

Unlike the original custom implementation, LangChain provides built‑in prompt templates
for each agent type. The `STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION` agent already
includes a prompt that instructs the LLM to follow the ReAct format, list available tools,
and output actions in a structured JSON format. Therefore no explicit system prompt is needed.

Usage:
    Ensure DEEPSEEK_API_KEY is set in .env or environment.
    Run: python agent_demo_langchain.py
"""

import os
from dotenv import load_dotenv
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

# Load environment variables
load_dotenv()

# 1. Define tools
def add_numbers(a: float, b: float) -> float:
    """对两个数字做加法运算"""
    return a + b

tool = StructuredTool.from_function(
    func=add_numbers,
    name="add_numbers",
    description="对两个数字做加法运算",
    args_schema=None,  # will infer from function signature
)

# 2. Configure DeepSeek LLM
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("DeepSeek API key not found. Please set DEEPSEEK_API_KEY environment variable.")

base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

llm = ChatOpenAI(
    model=model_name,
    openai_api_key=api_key,
    openai_api_base=base_url,
    temperature=0.1,
    max_tokens=2000,
)

# 3. Create ReAct agent
tools = [tool]

# LangChain's `initialize_agent` creates an agent with a default ReAct prompt tailored for
# structured chat (multi‑input tools). The prompt is automatically constructed from the
# tool descriptions and the agent type.
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=5,
    early_stopping_method="generate",
)

def main():
    """Run the agent with a sample query."""
    # Print the built‑in prompt template for inspection
    try:
        prompt = agent.agent.llm_chain.prompt
        print("=== Built‑in ReAct Prompt Template ===")
        if hasattr(prompt, 'messages'):
            for i, msg in enumerate(prompt.messages):
                print(f"\n--- Message {i} ({msg.__class__.__name__}) ---")
                print(msg.prompt.template if hasattr(msg.prompt, 'template') else msg.content)
        else:
            print(prompt)
        print("=" * 50)
    except AttributeError as e:
        print(f"Could not retrieve prompt template: {e}")

    user_input = "计算 123 加上 456 减去 789 的结果是多少？"
    result = agent.run(user_input)
    print(result)

if __name__ == "__main__":
    main()