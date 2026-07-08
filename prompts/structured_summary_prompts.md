# Structured Summary Prompts

## Purpose

This document records prompt versions for structured summary generation.

The output schema is:

```json
{
  "topic": "string",
  "summary": "string",
  "keywords": ["string"],
  "action_items": ["string"]
}
```

## Prompt Styles

### default

Purpose:

General structured summary.

Expected behavior:

- Topic should be Chinese
- Summary should be Chinese
- Keywords should be a list of strings
- Action items should be a list of strings
- Output must be valid JSON only

### concise

Purpose:

Generate a short and direct structured summary.

Expected behavior:

- Summary within 80 Chinese characters
- 3 to 5 keywords
- 1 to 3 short action items

### research

Purpose:

Generate a research-oriented structured analysis.

Expected behavior:

- Focus on concepts, methods, limitations, and study directions
- Keywords should be academic and precise
- Action items should help a graduate student continue studying the topic

### action

Purpose:

Generate an action-oriented learning plan.

Expected behavior:

- Focus on what the learner should do next
- Action items should be specific and executable
- Action items should be ordered from easy to hard

## Few-shot Example

```json
{
  "topic": "智能体开发基础",
  "summary": "这段文本说明智能体开发不仅是调用大模型，还需要掌握工程结构、工具调用、检索、评测和部署。",
  "keywords": ["智能体开发", "工程结构", "工具调用", "检索", "评测"],
  "action_items": ["整理项目结构", "练习工具调用", "设计简单评测集"]
}
```

## Experiment Notes

| Date       | Style    | Input               | Observation |
| ---------- | -------- | ------------------- | ----------- |
| 2026-07-08 | concise  | examples/sample.txt |             |
| 2026-07-08 | research | examples/sample.txt |             |
| 2026-07-08 | action   | examples/sample.txt |             |