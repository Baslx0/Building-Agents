# Learning Log

## Checkpoint — 18 Sep 2026

### What I am building

I am learning how AI agents work by building one from Python fundamentals instead of starting with an agent framework.

Long-term direction: a practical IT-oriented agent that can understand natural language, choose from controlled diagnostic tools, execute those tools through Python, and use the results to answer the user.

### What I learned

#### Functions can become tools

A normal Python function becomes useful to an agent when it has a clear input, performs a bounded task, and returns a useful result.

Current tools:

```python
greet(name)
ping_host(host)
```

#### `print` and `return` are different

`print()` displays a value to a human.

`return` gives a value back to the calling code and ends the current function immediately.

This led to learning early returns as a way to avoid unnecessary nesting.

#### A real system command can be wrapped by Python

The first real IT tool uses:

```python
subprocess.run(
    ["ping", "-n", "1", host],
    capture_output=True,
    text=True
)
```

Important observations:
- `subprocess` is a module.
- `run` is a function in that module.
- `stdout`, `stderr`, and `returncode` are values on the returned process result.
- `capture_output=True` captures command output; it does not mean the command succeeded.
- a return code of `0` usually means the process completed successfully according to that program.

#### Tool execution should happen once

An early router version could both print a tool call and return another call to the same tool. That would execute the tool twice.

This is harmless for a greeting but dangerous for tools with side effects.

Lesson: execute once, store the result, return it.

#### Parsing is not language understanding

The current router uses `.split()` and checks the first token.

It understands:

```text
ping google.com
```

but not:

```text
Can you check whether google.com is reachable?
```

This is the exact boundary between the current rule-based program and the upcoming LLM-driven decision layer.

#### Validate before execution

Input such as just `ping` originally caused an `IndexError` because `parts[1]` did not exist.

The current version checks input length before executing a tool.

### Current mental model

```text
Agent = Model + Instructions + Tools + State + Loop + Guardrails
```

The model should understand intent and choose an allowed action. The Python controller should validate that action. The Python tool should perform the real operation.

### Next

Use a small local LLM as the decision-making layer. Start with inference only, then structured output, then controlled tool calling.
