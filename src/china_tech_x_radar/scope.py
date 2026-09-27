"""Canonical AI-building scope shared by classifier and editorial preflight."""
from __future__ import annotations

import re

# This list represents the account's practical AI/building boundary. It deliberately
# excludes bare "AI"/"人工智能" so generic policy, finance or diplomacy stories do not
# enter the editorial queue merely for mentioning AI.
AI_BUILDING_SCOPE_TERMS = (
    "agent", "agents", "agentic", "coding", "code", "developer", "software development",
    "workflow", "automation", "automate", "productivity", "copilot", "computer use",
    "tool use", "eval", "evals", "evaluation", "benchmark", "verification", "verify",
    "reliability", "reasoning", "inference", "context", "memory", "multi-agent",
    "multi agent", "orchestration", "runtime", "harness", "subagent", "subagents",
    "llm", "world model", "world models", "reinforcement learning",
    "recursive self-improvement", "ai research", "fine-tuning", "fine tuning",
    "local model", "local llm", "prompt", "token", "kv cache", "mcp", "rag",
    "openai", "anthropic", "claude", "codex", "cursor", "devin", "qwen",
    "deepseek", "kimi", "glm", "mimo", "jev", "gpt", "opus", "gemini", "grok",
    "astra", "fable",
    "智能体", "代理", "编程", "代码", "开发者", "软件开发", "自动化", "工作流",
    "生产力", "评测", "基准", "验证", "可靠性", "推理", "推理成本", "上下文",
    "记忆", "多智能体", "世界模型", "大模型", "本地模型", "本地部署",
    "训练", "微调", "强化学习", "递归自我改进", "人工智能研究", "提示词", "缓存",
)


def ai_building_scope_matches(text: str | None) -> bool:
    value = str(text or "").casefold()
    for term in AI_BUILDING_SCOPE_TERMS:
        t = term.casefold()
        if re.search(r"[㐀-鿿]", t):
            if t in value:
                return True
        else:
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])"
            if re.search(pattern, value):
                return True
    return False
