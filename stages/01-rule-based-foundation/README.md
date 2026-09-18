# Stage 01 — Rule-Based Foundation

This stage is the first meaningful agent-building milestone. It intentionally groups the earlier Python exercises into one final checkpoint instead of keeping a new file for every small change.

## What this stage contains

The final `agent.py` combines the concepts learned so far:

- functions, parameters, and f-strings
- `print()` vs `return`
- early-return thinking
- importing and using `subprocess`
- wrapping a real Windows command as `ping_host(host)`
- reading a process return code
- defining multiple tools
- parsing simple user commands with `.split()`
- routing to the correct tool
- passing arguments dynamically
- basic input validation
- returning a controlled error for unsupported tools

## What it can understand

```text
ping google.com
greet Basil
```

## Current limitation

The program does not understand natural language. The decision is still encoded in rules such as:

```python
if parts[0] == keywords[0]:
```

That limitation defines the boundary of Stage 01.

## Next stage

Stage 02 adds a small local LLM so the decision layer can begin understanding requests such as:

```text
Can you check whether google.com is reachable?
```

The Python tool—not the LLM—will still perform the real operation.
