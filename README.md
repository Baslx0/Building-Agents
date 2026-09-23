# Building Agents

A learning-by-building repository documenting my path from Python fundamentals to a real tool-using AI agent.

The goal is not to create a new file for every exercise or hide the mechanics behind an agent framework. Each **stage** represents a meaningful milestone and contains the best working checkpoint reached after learning several related concepts.

## Current status

**Stage 01 — Rule-Based Foundation — Complete**  
**Stage 02 — Local LLM Integration — In Progress**

The project has now moved beyond hard-coded routing and can communicate with a real local LLM through Ollama.

```text
User
  ↓
Python
  ↓
Ollama
  ↓
Phi-4-mini
  ↓
Assistant response
```

Stage 02 currently supports system instructions, conversation history, and a continuous chat loop.

## Stages

```text
01  Rule-Based Foundation       COMPLETE
02  Local LLM Integration      IN PROGRESS
03  Structured Tool Calling
04  Agent Loop
05  State, Memory & Guardrails
06  Practical IT Agent
07  Local vs Cloud API
```

Stages are intentionally broad. Small exercises, bugs, and discoveries are recorded in [LEARNING_LOG.md](LEARNING_LOG.md) instead of creating dozens of tiny source files.

## Repository layout

```text
Building-Agents/
|-- README.md
|-- ROADMAP.md
|-- LEARNING_LOG.md
`-- stages/
    |-- 01-rule-based-foundation/
    |   |-- README.md
    |   `-- agent.py
    `-- 02-local-llm/
        |-- README.md
        `-- chat.py
```

## Learning principles

1. Build from first principles before adding frameworks.
2. Group related learning into meaningful stages.
3. Keep one useful code checkpoint per stage instead of one file per exercise.
4. The LLM decides; controlled Python tools execute.
5. Validate model decisions before executing tools.
6. Do not give a model unrestricted shell access.
7. Use Git history and the learning log to preserve the journey.

See [ROADMAP.md](ROADMAP.md) for the full path.
