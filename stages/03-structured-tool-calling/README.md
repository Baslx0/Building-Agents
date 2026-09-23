# Stage 03 — Structured Tool Calling

**Status: In Progress**

This stage now supports both controlled real tool execution and normal model replies.

## Current flow

```text
User request
    ↓
Phi-4-mini
    ↓
Structured JSON decision
    ↓
json.loads()
    ↓
Python controller
    ↓
    ├─ tool selected → validate registry + arguments → execute tool
    └─ tool = null   → print normal model response
```

## Tool registry

The controller now uses a Python dictionary as a registry:

```python
tools = {
    "ping_host": ping_host
}
```

The model returns a tool name such as:

```json
{
  "tool": "ping_host",
  "arguments": {
    "host": "google.com"
  },
  "message": null
}
```

Python then uses the model's choice as the registry key:

```python
selected_tool = tools[decision["tool"]]
```

That retrieves the real Python function, which can then be executed.

## No-tool path

The model is also allowed to decide that no real tool is needed:

```json
{
  "tool": null,
  "arguments": {},
  "message": "A normal user-facing response."
}
```

In that case, Python prints `message` and does not execute anything.

## Rules learned

- the LLM proposes a tool name
- Python validates that the tool exists in the registry
- the registry maps the tool name to a real Python function
- the model must not invent unavailable tools
- normal questions can be answered through `message`
- real system actions require a registered tool
- internal registry details should not be exposed in user-facing replies

## Current limitation

Stage 03 still only has one real tool and basic argument validation. The next steps are stronger validation, another tool, and feeding tool results back into the model.
