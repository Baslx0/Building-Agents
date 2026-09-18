# Building Agents

A learning-by-building repository documenting my path from Python fundamentals to a real tool-using AI agent.

The goal is **not** to hide agent behavior behind a framework. I am building the important pieces from first principles so I understand what the model does, what Python does, and what the tools actually execute.

## Current checkpoint

**Phase 04 — Rule-Based Tool System**

The current program can:
- expose Python functions as tools
- execute a real Windows `ping` through `subprocess`
- route commands to `ping_host()` or `greet()`
- parse simple commands such as `ping google.com`
- validate missing/invalid input
- return tool results cleanly

It is **not an AI agent yet**. Tool selection is still based on Python rules such as `if parts[0] == "ping"`.

## Architecture

```text
Current

User
  |
  v
Input Validation
  |
  v
Command Parser
  |
  v
Rule-Based Router
  |-----------------|
  v                 v
ping_host()       greet()
  |                 |
  +--------+--------+
           |
           v
         Result
```

Next target:

```text
User
  |
  v
Local LLM  <-- understands intent and chooses a tool
  |
  v
Python Controller  <-- validates the model decision
  |
  v
Tool Registry
  |-- ping_host()
  |-- greet()
  |-- DNS / HTTP tools later
  |
  v
Tool Result
  |
  v
Local LLM
  |
  v
Final Response
```

The model is the **decision maker**, not the executor. The model may decide to call `ping_host(host="google.com")`, but the Python function performs the real ping.

## Learning roadmap

- [x] Python functions and parameters
- [x] `print` vs `return`
- [x] early returns
- [x] modules, functions, methods, and attributes
- [x] `subprocess.run()`
- [x] stdout, stderr, and return codes
- [x] first real IT tool: `ping_host()`
- [x] manual tool routing
- [x] command parsing with `.split()`
- [x] basic input validation
- [ ] run a small local LLM
- [ ] structured model decisions
- [ ] tool registry
- [ ] LLM-driven tool calling
- [ ] agent loop
- [ ] memory / state
- [ ] guardrails and stronger validation
- [ ] expand into a practical IT support / operations agent
- [ ] compare local inference with a cloud LLM API

See [ROADMAP.md](ROADMAP.md) for the phase-by-phase plan and [LEARNING_LOG.md](LEARNING_LOG.md) for what I learned along the way.

## Repository layout

```text
Building-Agents/
|-- README.md
|-- ROADMAP.md
|-- LEARNING_LOG.md
|-- src/
|   `-- rule_based_agent.py
`-- examples/
    |-- 01-first-tool/
    |   `-- ping_tool.py
    `-- 02-manual-router/
        `-- router.py
```

Future checkpoints will be added instead of replacing the learning history.

## Why a local model first?

The next phase intentionally uses a **small local model** before a hosted LLM API. This keeps the architecture visible: model, controller, tools, validation, and execution remain separate pieces.

A cloud API can be introduced later without redesigning the whole agent; ideally only the inference layer changes.

## Principles

1. Understand the mechanism before adding frameworks.
2. The LLM chooses; Python tools execute.
3. Validate model output before executing tools.
4. Never give a model unrestricted shell access just because it can choose tools.
5. Keep each checkpoint small enough to understand.
6. Preserve lessons and failed ideas, not only final code.

## Current commands

```text
ping google.com
greet Basil
```

Natural-language requests such as `Can you check whether google.com is reachable?` are intentionally not supported yet. That limitation is what the next local-LLM phase will solve.

## Environment

The current ping implementation uses Windows `ping -n 1` syntax. Cross-platform handling can be added later.

## Status

Learning project — actively evolving.
