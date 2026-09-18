# Building Agents

A learning-by-building repository documenting my path from Python fundamentals to a real tool-using AI agent.

The goal is not to create a new file for every exercise or hide the mechanics behind an agent framework. Each **stage** represents a meaningful milestone and contains the best working checkpoint reached after learning several related concepts.

## Current status

**Stage 01 — Rule-Based Foundation — Complete**

The current checkpoint has real Python tools, command parsing, routing, and basic validation. It is not an AI agent yet because Python rules still decide which tool to use.

```text
User
  |
  v
Parser + Validation
  |
  v
Rule-Based Decision
  |----------------|
  v                v
ping_host()      greet()
  |                |
  +-------+--------+
          |
          v
        Result
```

Next:

```text
User
  |
  v
Local LLM        <-- understands intent
  |
  v
Python Controller
  |
  v
Allowed Tools    <-- perform the real actions
  |
  v
Tool Result
  |
  v
Final Response
```

The model will be the decision maker; Python tools remain the executors.

## Stages

```text
01  Rule-Based Foundation       COMPLETE
02  Local LLM                   NEXT
03  Structured Tool Calling
04  Agent Loop
05  State, Memory & Guardrails
06  Practical IT Agent
07  Local vs Cloud API
```

Stages are intentionally broad. Small exercises, bugs, and discoveries are recorded in [LEARNING_LOG.md](LEARNING_LOG.md) rather than creating dozens of tiny source files.

## Repository layout

```text
Building-Agents/
|-- README.md
|-- ROADMAP.md
|-- LEARNING_LOG.md
`-- stages/
    `-- 01-rule-based-foundation/
        |-- README.md
        `-- agent.py
```

New stage directories are created only when a meaningful milestone is reached.

## Stage 01 capabilities

The current program can accept commands such as:

```text
ping google.com
greet Basil
```

It combines the earlier lessons around functions, return values, `subprocess`, tools, parsing, routing, and validation into one checkpoint.

Natural-language requests such as:

```text
Can you check whether google.com is reachable?
```

are intentionally not supported yet. That is the problem Stage 02 will address.

## Learning principles

1. Build from first principles before adding frameworks.
2. Group related learning into meaningful stages.
3. Keep one useful code checkpoint per stage instead of one file per exercise.
4. The LLM decides; controlled Python tools execute.
5. Validate model decisions before executing tools.
6. Do not give a model unrestricted shell access.
7. Use Git history and the learning log to preserve the journey.

## Environment

Stage 01 currently uses Windows `ping -n 1` syntax.

See [ROADMAP.md](ROADMAP.md) for where the project is going.
