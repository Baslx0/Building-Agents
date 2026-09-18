# Learning Log

This file preserves the small lessons, experiments, mistakes, and discoveries that lead to each stage. The source tree intentionally does **not** keep a separate Python file for every exercise.

## Stage 01 — Rule-Based Foundation

**Checkpoint: 18 Sep 2026**

The first stage started with basic Python functions and ended with a working rule-based tool system.

### Functions became tools

A function with a clear input, bounded action, and useful returned result can become an agent tool.

Current tools: `greet(name)` and `ping_host(host)`.

### `print()` vs `return`

`print()` displays something to the human. `return` gives a value back to the calling code and immediately ends the current function.

This also introduced early-return thinking and helped reduce unnecessary nesting.

### First real system operation

`ping_host(host)` wraps Windows ping with `subprocess.run()`.

Learned that `subprocess` is a module and `run` is a function in it; `capture_output=True` captures stdout/stderr rather than indicating success; `text=True` returns text instead of bytes; and `returncode` reports process exit status.

### Execute a tool once

An early router version could call a tool while printing it and then call it again while returning it. That is harmless for `greet()`, but a side-effecting tool could perform the action twice.

Lesson: execute once, keep the result, return it.

### Manual routing to command parsing

A numeric menu first selected between the tools. It was then replaced by simple commands:

```text
ping google.com
greet Basil
```

This introduced `.split()`, list indexes, routing, and dynamic arguments.

### Validation

Trying `ping` without a target exposed an `IndexError`, which introduced validation with `len(parts)`. Empty input reinforced the rule: validate before accessing indexes.

### Truthiness

An experiment with `if user_input == True:` exposed the difference between a non-empty string and Boolean `True`, introducing Python truthy/falsy values.

### Accidental recursion

One early error path called `select_tool()` from inside itself. This introduced recursion and why repeatedly calling the router from its own error branch can eventually cause a `RecursionError`.

### Parser vs agent

The final Stage 01 program understands explicit commands but not natural language:

```text
ping google.com                         -> understood
Can you check if google.com is alive?  -> not understood
```

That boundary defines the next stage.

### Mental model

```text
Agent = Model + Instructions + Tools + State + Loop + Guardrails
```

The model should understand intent and choose an allowed action. The Python controller should validate the choice. The Python tool should perform the real operation.

**Next: Stage 02 — Local LLM.**
