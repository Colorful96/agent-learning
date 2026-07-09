# Agent Learning

这是智能体开发学习路线的练习项目。

## 当前目标

做一个命令行文本摘要与结构化分析工具：

1. 用户输入文本，或传入本地文件
2. 程序调用 DeepSeek 生成摘要
3. 支持普通摘要和结构化 JSON 输出
4. 支持多种 prompt 风格
5. 支持对结构化输出做简单规则评测

## 运行方式

先复制 `.env.example` 为 `.env`，然后把 `DEEPSEEK_API_KEY` 改成自己的 API key。

```powershell
.venv\Scripts\Activate.ps1
```

查看命令帮助：

```powershell
python -m src.main --help
```

### 普通摘要

手动输入文本：

```powershell
python -m src.main
```

摘要一个文本文件：

```powershell
python -m src.main examples\sample.txt
```

摘要复杂样例：

```powershell
python -m src.main examples\agent_complex.txt
```

程序会输出：

```text
outputs/summary.md
```

### 结构化摘要

默认结构化输出：

```powershell
python -m src.main examples\agent_complex.txt --structured
```

指定 prompt 风格：

```powershell
python -m src.main examples\agent_complex.txt --structured --style research
```

一次生成全部风格：

```powershell
python -m src.main examples\agent_complex.txt --structured --style all
```

支持的风格：

```text
default
concise
research
action
all
```

结构化输出会生成 Markdown 和 JSON 文件，例如：

```text
outputs/structured_summary_research.md
outputs/structured_summary_research.json
```

### 评测结构化输出

先生成结构化结果：

```powershell
python -m src.main examples\agent_complex.txt --structured --style all
```

再运行评测：

```powershell
python -m src.core.evaluator
```

评测报告会保存到：

```text
outputs/evaluation_report.json
```

### 工具函数 Demo

直接测试本地工具函数：

```powershell
python -m src.demos.tool_demo
```

测试工具注册表：

```powershell
python -m src.demos.tool_registry_demo
```

如果没有配置 DeepSeek API key，程序会自动使用本地规则摘要，方便先跑通流程。

运行日志会保存到：

```text
outputs/app.log
```

## 项目结构

```text
agent_learning/
├── README.md
├── day1.md
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── examples/
│   ├── sample.txt
│   └── agent_complex.txt
├── prompts/
│   └── structured_summary_prompts.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── clients/
│   │   ├── __init__.py
│   │   └── llm_client.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── evaluator.py
│   │   └── summarizer.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── local_tools.py
│   │   └── registry.py
│   └── demos/
│       ├── __init__.py
│       ├── tool_demo.py
│       └── tool_registry_demo.py
└── outputs/
```

## 当前能力

```text
文本输入
UTF-8 文本文件输入
docx 文件输入
DeepSeek API 调用
普通摘要
结构化 JSON 输出
多风格 prompt
Markdown 输出
JSON 输出
结构化输出规则评测
本地工具函数
工具注册表
日志记录
```

## 学习重点

这个项目当前覆盖：

```text
Python 项目结构
虚拟环境
.env 配置
HTTP API 调用
Prompt Engineering
Few-shot Prompting
结构化输出
Pydantic 校验
命令行参数 argparse
简单规则评测
Git 版本管理
```
