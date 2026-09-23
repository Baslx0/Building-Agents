# Stage 03 — Structured Tool Calling

**Status: In Progress**

This stage is the first point where the local LLM stops being only a chatbot and begins acting as a decision layer for real Python tools.

## Current flow

```text
Natural-language request
        ↓
Phi-4-mini
        ↓
Structured JSON decision
        ↓
json.loads()
        ↓
Python dictionary
        ↓
Tool + argument validation
        ↓
Approved Python tool
        ↓
Real system result
```

## Current example

User:

```text
can u ping 8.8.8.8 ?
```

Model decision:

```json
{
  "tool": "ping_host",
  "arguments": {
    "host": "8.8.8.8"
  }
}
```

Python then validates the tool name and required `host` argument before calling:

```python
ping_host(host)
```

## Concepts learned

- structured model output
- `format="json"` with Ollama
- JSON text vs Python dictionaries
- `json.loads()`
- reading nested values such as `decision["arguments"]["host"]`
- validating a model decision before execution
- keeping the LLM as the decision maker while Python remains the controller
- executing a real bounded tool only after validation

## Current limitation

The validation is intentionally simple and only supports one tool:

```text
ping_host(host)
```

The project does not yet have:
- a tool registry
- robust malformed-JSON handling
- schema validation
- multiple tools
- tool-result feedback back into the LLM
- a full agent reasoning/execution loop

Those are the next milestones.
