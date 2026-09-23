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


---

## Stage 02 — Local LLM Integration

**Checkpoint: 23 Sep 2026**

Stage 02 started by replacing the hard-coded language layer with a real local LLM.

### Local runtime vs model

The architecture was separated clearly:

```text
Phi-4-mini = model / brain
Ollama     = runtime + API interface
Python     = controller/application
```

A key correction was learning that Ollama does not understand the user's intent itself; the LLM does. Ollama runs the model and exposes an interface to Python.

### Chat schema

Using `ollama.chat()` introduced the message format:

```python
{
    "role": "user",
    "content": "..."
}
```

The important idea is that the API/interface defines the request schema. The model and runtime are separate concepts.

### System instructions

A `system` message was added to control the assistant's behavior:

```text
system    = instructions / behavior
user      = user message
assistant = model reply
```

### Conversation state

A Python list named `chats_history` became the current conversation state.

The program now:
1. starts with the system instruction
2. appends the user message
3. sends the full history to the model
4. appends the assistant reply
5. repeats

This demonstrated that the model does not magically remember previous calls; the application must send the previous context again.

### Functions and continuous chat

The chat flow was wrapped in `Chat_agent(user_input)`, then placed inside a `while True` loop.

An important logic detail was checking for `exit` **before** sending the message to the model, so the model does not waste inference on an exit command.

### LLM vs RAG vs tools

The current program only has a local LLM plus instructions and conversation history.

```text
LLM   = generates from learned model knowledge
RAG   = retrieves external knowledge and gives it to the LLM
Tools = Python functions/actions that interact with the real system
```

### First look inside the model

The current understanding of the input pipeline is:

```text
Text
↓
Tokens
↓
Token IDs
↓
Embeddings
↓
Processed using learned weights
```

Important corrections:
- a token is a piece of text, not necessarily a full word
- a token ID is only an identifier
- an embedding is a numeric vector representation
- an embedding does not turn into weights
- weights are learned parameters already inside the trained model and are used during inference

### Current checkpoint

The project now has a stateful local chatbot running entirely through Python + Ollama + Phi-4-mini.

Next learning topic: **attention and transformer context processing**, before moving into structured tool calling.
