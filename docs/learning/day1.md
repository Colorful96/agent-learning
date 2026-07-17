# Day 1 - Python 工程基础与 DeepSeek 摘要工具

> 这是项目早期的学习记录。当前应用入口和最新项目结构请以根目录 README.md 为准。

## 今日目标

今天的目标不是直接做复杂智能体，而是先搭好一个可运行、可维护的小型 Python 项目。

最终完成的小工具：

```text
命令行文本摘要工具

能力：
1. 支持手动输入文本
2. 支持读取 txt 文件
3. 支持调用 DeepSeek API 生成摘要
4. DeepSeek 调用失败时自动回退到本地规则摘要
5. 将摘要保存为 Markdown 文件
6. 记录运行日志
7. 使用 Git 进行版本管理
```

## 当前项目位置

```text
D:\智能体开发\agent_learning
```

## 项目结构

```text
agent_learning/
├── day1.md
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── examples/
│   └── sample.txt
├── src/
│   ├── main.py
│   ├── config.py
│   ├── summarizer.py
│   └── llm_client.py
└── outputs/
    ├── summary.md
    └── app.log
```

## 1. 虚拟环境 venv

创建虚拟环境的命令：

```powershell
python -m venv .venv
```

含义：

```text
给当前项目创建一个独立的 Python 环境。
```

激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

它和 conda 的作用类似：

```powershell
conda activate 环境名
```

共同点：

```text
都用于隔离 Python 解释器和第三方依赖。
```

区别：

```text
venv 更轻量，是 Python 官方自带工具。
conda 更重，可以管理更多科学计算和系统级依赖。
```

今天已经将项目虚拟环境切换到：

```text
Python 3.11.10
```

## 2. PowerShell 的 New-Item

`New-Item` 是 PowerShell 里创建文件或文件夹的命令。

例如：

```powershell
New-Item README.md
```

表示创建一个 `README.md` 文件。

今天创建过的关键文件：

```text
README.md：项目说明
requirements.txt：项目依赖
.env：私密配置文件
.env.example：配置模板
.gitignore：Git 忽略规则
src/main.py：程序入口
src/config.py：配置读取
src/summarizer.py：摘要逻辑
src/llm_client.py：大模型 API 调用
```

## 3. requirements.txt

当前直接依赖：

```text
pydantic==2.5.3
python-dotenv==0.21.1
requests==2.31.0
```

含义：

```text
requests：发送 HTTP 请求，调用 DeepSeek API
python-dotenv：读取 .env 配置文件
pydantic：定义和校验数据结构
```

安装依赖：

```powershell
pip install -r requirements.txt
```

## 4. .env 和 .env.example

`.env.example` 是配置模板：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_API_BASE=https://api.deepseek.com
```

`.env` 是真正保存私密配置的文件。

注意：

```text
.env 不能上传 GitHub
.env 不能发给别人
.env 不应该截图公开
```

所以 `.gitignore` 里写了：

```gitignore
.env
```

## 5. main.py 的职责

`main.py` 是程序入口，负责组织整体流程。

当前主流程：

```text
1. 读取配置
2. 初始化日志
3. 读取用户输入或 txt 文件
4. 调用摘要函数
5. 保存 Markdown
6. 打印结果
```

核心思想：

```text
main.py 管流程，不负责具体摘要算法，也不直接处理 API 请求细节。
```

## 6. config.py 的职责

`config.py` 负责读取配置和组织项目路径。

它读取：

```text
DeepSeek API key
DeepSeek 模型名
DeepSeek API 地址
outputs 目录
日志文件路径
```

关键思想：

```text
配置不要写死在业务代码里，统一交给 config.py 管理。
```

## 7. llm_client.py 的职责

`llm_client.py` 负责调用 DeepSeek API。

它做的事情：

```text
1. 检查 API key
2. 拼接请求地址 /chat/completions
3. 组织 headers
4. 组织 payload
5. 使用 requests.post 发送请求
6. 检查 HTTP 状态码
7. 解析 JSON 响应
8. 返回模型生成的文本
```

DeepSeek 请求地址：

```text
https://api.deepseek.com/chat/completions
```

核心函数：

```python
generate_text(api_key, model, api_base, system_prompt, user_input)
```

核心思想：

```text
把复杂的 HTTP API 调用封装成一个简单函数。
```

## 8. summarizer.py 的职责

`summarizer.py` 负责摘要逻辑。

它包含两种摘要方式：

```text
1. DeepSeek API 摘要
2. 本地规则摘要
```

当前逻辑：

```text
优先调用 DeepSeek API
如果 API 调用失败，回退到本地规则摘要
```

这叫 fallback，也就是兜底方案。

核心思想：

```text
外部 API 可能失败，程序要有备用方案，不能轻易崩掉。
```

## 9. 命令行参数和文件读取

今天新增了 txt 文件输入功能。

直接输入文本：

```powershell
python src\main.py
```

读取文件摘要：

```powershell
python src\main.py examples\sample.txt
```

相关知识：

```text
sys.argv：读取命令行参数
Path：处理文件路径
```

例如：

```powershell
python src\main.py examples\sample.txt
```

此时：

```text
sys.argv[0] = src\main.py
sys.argv[1] = examples\sample.txt
```

当前输入流程：

```text
如果没有传文件路径：让用户手动输入文本
如果传了文件路径：读取该 txt 文件内容
```

核心思想：

```text
把输入来源封装到 read_input_text()，让主流程保持干净。
```

## 10. 异常处理

异常处理用于让程序遇到错误时不要直接崩溃。

今天处理了几类错误：

```text
输入为空
文件不存在
输入路径不是文件
DeepSeek API key 没配置
网络失败
DeepSeek 返回错误
```

`main.py` 里处理用户输入错误：

```python
except ValueError as error:
    logger.warning("Invalid input: %s", error)
    print(f"输入错误：{error}")
```

`summarizer.py` 里处理模型 API 错误：

```python
except LLMClientError as error:
    logger.warning("DeepSeek API failed, falling back to local rule: %s", error)
    return summarize_text_locally(cleaned_text)
```

核心思想：

```text
不同错误要分开处理。
用户输入错了，就提示用户。
API 失败了，就记录日志并使用 fallback。
```

## 11. 自定义异常 LLMClientError

`llm_client.py` 中定义了：

```python
class LLMClientError(Exception):
    pass
```

它表示：

```text
大模型 API 调用相关错误。
```

好处：

```text
可以明确区分模型调用错误和用户输入错误。
```

## 12. 日志 logging

日志用于记录程序运行过程。

日志文件：

```text
outputs/app.log
```

查看日志：

```powershell
Get-Content outputs\app.log -Tail 10
```

实时查看日志：

```powershell
Get-Content outputs\app.log -Wait
```

常见日志等级：

```text
DEBUG：调试细节
INFO：正常运行信息
WARNING：有问题，但程序还能继续
ERROR：功能失败
CRITICAL：严重错误
```

今天记录的日志包括：

```text
摘要保存路径
摘要来源 deepseek_api 或 local_rule
DeepSeek API 失败原因
用户输入错误原因
```

核心思想：

```text
异常处理负责让程序不轻易崩掉。
日志负责让我们知道发生了什么。
```

## 13. Git 版本管理

今天使用 Git 管理项目版本。

常用命令：

```powershell
git status
git add .
git commit -m "提交说明"
```

今天的关键提交包括：

```text
init project
add OpenAI API summarizer
switch summarizer to DeepSeek API
add logging for summarizer
simplify requirements for Python 3.11
support summarizing text files
```

其中 OpenAI 版本后来已经切换为 DeepSeek。

## 14. 当前运行方式

进入项目：

```powershell
cd D:\智能体开发\agent_learning
```

激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

检查 Python 版本：

```powershell
python --version
```

应显示：

```text
Python 3.11.10
```

手动输入摘要：

```powershell
python src\main.py
```

文件摘要：

```powershell
python src\main.py examples\sample.txt
```

查看输出：

```powershell
Get-Content outputs\summary.md
```

查看日志：

```powershell
Get-Content outputs\app.log -Tail 10
```

## 15. 今日最重要的工程思想

```text
main.py 管流程
config.py 管配置
llm_client.py 管模型 API 调用
summarizer.py 管摘要业务逻辑
```

以及：

```text
把复杂能力封装成简单函数。
把容易变化的部分隔离出来。
外部服务可能失败，要有异常处理和 fallback。
程序运行过程要写日志，方便排查问题。
```

## 16. 当前在 8 周路线中的位置

现在处于：

```text
第 1 周：工程基础与环境搭建
```

完成度：

```text
约 90%
```

已经完成：

```text
项目结构
虚拟环境
依赖安装
.env 配置
DeepSeek API 调用
异常处理
日志记录
txt 文件输入
Markdown 输出
Git 版本管理
```

下一步：

```text
进入第 2 周：Prompt + 结构化输出
```

第 2 周会把当前的普通文本摘要升级成结构化结果，例如：

```json
{
  "topic": "...",
  "summary": "...",
  "keywords": ["...", "..."],
  "action_items": ["...", "..."]
}
```
