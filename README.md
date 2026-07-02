# Agent Learning

这是智能体开发学习路线第 1 周的小项目。

## 当前目标

做一个命令行文本摘要工具：

1. 用户输入一段文本
2. 程序生成摘要
3. 摘要保存到 `outputs/summary.md`

## 运行方式

先复制 `.env.example` 为 `.env`，然后把 `OPENAI_API_KEY` 改成自己的 API key。

```powershell
.venv\Scripts\Activate.ps1
python src\main.py
```

如果没有配置 API key，程序会自动使用本地规则摘要，方便先跑通流程。

## 项目结构

```text
agent_learning/
├── README.md
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── src/
│   ├── main.py
│   ├── config.py
│   ├── openai_client.py
│   └── summarizer.py
└── outputs/
```
