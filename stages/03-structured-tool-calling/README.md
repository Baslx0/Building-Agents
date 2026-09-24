# Stage 03 — Structured Tool Calling

**Status: In Progress**

This stage now separates the agent controller, executable tools, system instructions, and persistent conversation data.

## Current structure

```text
03-structured-tool-calling/
├── README.md
└── agent-1/
    ├── agent.py
    ├── tools.py
    ├── prompts/
    │   └── system.md
    └── data/
        └── chat_history.json
```

## Responsibility split

```text
agent.py
= controller/runtime

tools.py
= executable capabilities

prompts/system.md
= agent behavior + routing instructions

data/chat_history.json
= persistent user/assistant conversation history
```

The system prompt is intentionally kept separate from conversation history. At runtime, `agent.py` loads both and builds the context sent to Phi-4-mini.

## Current flow

```text
system.md
    ↓
agent.py loads instructions

chat_history.json
    ↓
agent.py loads conversation state

User request
    ↓
Phi-4-mini
    ↓
Structured JSON decision
    ↓
Python controller
    ↓
    ├─ tool selected → registry validation → execute tool
    └─ tool = null   → print normal model response
```

## Tool registry

The controller currently uses:

```python
tools = {
    "ping_host": ping_host
}
```

The model's tool choice becomes the registry key:

```python
selected_tool = tools[decision["tool"]]
```

## Persistent history

Conversation history is stored as JSON rather than being mixed with system instructions:

```json
[
  {
    "role": "user",
    "content": "..."
  },
  {
    "role": "assistant",
    "content": "..."
  }
]
```

The controller loads this history at startup and saves it after each model response.

## Current limitation

Stage 03 still has one real tool and basic argument validation. The next steps are richer tool metadata, stronger validation, and more tools.
