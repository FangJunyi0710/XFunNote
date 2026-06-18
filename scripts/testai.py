import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
	api_key=os.environ.get("DEEPSEEK_API_KEY"),
	base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
	model="deepseek-v4-pro",
	messages=[
		{"role": "system", "content": "你是一个个人效率助手，帮助用户整理计划和生成日报。"},
		{"role": "user", "content": "今天学习了Python虚拟环境配置。"}
	],
	extra_body={"thinking": {"type": "disabled"}},
	reasoning_effort="high",
	stream=False,
	# max_tokens=500,
	# temperature=0.5,
    # response_format
    # tools=tools,
    # tool_choice="auto",
    # logprobs=true, 
    # top_logprobs
)

print(response.choices[0].message.content)

print(response)

# ChatCompletion(id='3c02ee2f-b4e2-4e39-9f31-61c2edf043ea', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='好的，我帮你把今天的学习内容整理成一份清晰的日报。\n\n---\n\n### 今日学习日报\n\n**日期：** [在此处填写日期，例如：2023年10月27日]\n**主题：** Python 虚拟环境配置\n\n#### 一、 学习内容与核心概念\n\n虚拟环境是 Python 开发中用于隔离项目依赖的关键工具。它能为每个项目创建一个独立的 Python 运行环境，解决不同项目间依赖库版本冲突的问题。\n\n**1. 什么是虚拟环境？**\n一种在项目内部创建的、包含特定 Python 解释器和第三方库的独立环境。在这个环境中安装的库不会影响系统全局的 Python 环境或其他项目。\n\n**2. 核心优势：**\n*   **依赖隔离与冲突解决：** 项目 A 需要 `Django 2.2`，项目 B 需要 `Django 4.0`，两者可在各自的虚拟环境中并存。\n*   **环境干净清晰：** 仅包含项目实际需要的库，便于通过 `requirements.txt` 文件记录和复现环境。\n*   **权限友好：** 无需管理员权限即可在用户目录下安装和管理 Python 包。\n\n#### 二、 实践操作步骤\n\n**1. 创建虚拟环境**\nPython 3.3+ 内置了 `venv` 模块，这是我今天学习使用的工具。\n```bash\n# 在项目根目录下执行，创建一个名为 .venv 的虚拟环境目录\npython3 -m venv .venv\n```\n\n**2. 激活与退出虚拟环境**\n激活后，命令行前会出现环境名称标识。\n\n*   **macOS / Linux 激活：**\n    ```bash\n    source .venv/bin/activate\n    ```\n*   **Windows 激活：**\n    ```bash\n    .\\.venv\\Scripts\\activate\n    ```\n*   **退出环境 (在所有系统中通用):**\n    ```bash\n    deactivate\n    ```\n\n**3. 管理与记录依赖**\n这是确保项目可复现的核心步骤。\n```bash\n# 在激活的虚拟环境中安装库\npip install requests flask\n\n# 将当前环境所有库及版本导出到 requirements.txt 文件\npip freeze > requirements.txt\n```\n生成的 `requirements.txt` 文件内容示例：\n```\nflask==2.3.3\nrequests==2.31.0\n... 以及其他依赖库\n```\n\n**4. 复现环境**\n拿到项目后，只需一条命令即可恢复完全一致的开发环境。\n```bash\n# 从 requirements.txt 文件安装所有依赖\npip install -r requirements.txt\n```\n\n#### 三、 最佳实践与建议\n\n*   **命名：** 环境目录通常命名为 `.venv` 或 `venv`，`.venv` 开头加点使其在文件系统中隐藏。\n*   **.gitignore 配置：** 必须将虚拟环境目录 `/ .venv` 加入 `.gitignore` 文件中，避免将其提交到版本控制系统。只需共享 `requirements.txt` 文件。\n*   **工具选择：** 今天学习了内置的 `venv`，未来可以探索功能更丰富的第三方工具如 `virtualenv`, `poetry`, `pipenv`。\n\n#### 四、 今日学习产出\n\n*   [x] 理解虚拟环境的核心价值与使用场景。\n*   [x] 掌握使用 `venv` 从创建、激活到退出的完整生命周期。\n*   [x] 学会使用 `pip freeze` 和 `requirements.txt` 进行环境导出与复现。\n*   [x] 了解虚拟环境相关的版本控制最佳实践。\n\n---\n**明日计划：** [可选填写，例如：练习在虚拟环境中创建第一个 Flask 应用]', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None))], created=1781532937, model='deepseek-v4-pro', object='chat.completion', moderation=None, service_tier=None, system_fingerprint='fp_9954b31ca7_prod0820_fp8_kvcache_20260402', usage=CompletionUsage(completion_tokens=786, prompt_tokens=24, total_tokens=810, completion_tokens_details=None, prompt_tokens_details=PromptTokensDetails(audio_tokens=None, cached_tokens=0), prompt_cache_hit_tokens=0, prompt_cache_miss_tokens=24))