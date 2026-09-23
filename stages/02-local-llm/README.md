# Stage 02 — Local LLM Integration

**Status: In Progress**

This stage connects Python to a local language model and introduces the first real LLM-driven conversation flow.

## Current stack

```text
Python
  ↓
Ollama
  ↓
Phi-4-mini
  ↓
Response
```

## Roles

```text
Phi-4-mini = model / brain
Ollama     = local runtime + API interface
Python     = application/controller
```

## What has been learned so far

- installing and running Ollama locally
- running `phi4-mini`
- calling the model from Python with `ollama.chat()`
- understanding `model` and `messages`
- understanding chat message schema:
  - `system`
  - `user`
  - `assistant`
- keeping conversation state in a Python list
- using `.append()` to add user and assistant messages
- sending the full conversation history back to the model
- wrapping chat behavior in a Python function
- using `while True` for a continuous conversation
- using `break` for a clean exit

## Current conversation flow

```text
system instruction
      ↓
user input
      ↓
append user message
      ↓
send chats_history to Ollama
      ↓
Phi-4-mini generates assistant reply
      ↓
append assistant reply
      ↓
return + print
      ↓
repeat
```

## Important distinction

The current program is still not using RAG or tools.

```text
LLM knowledge = learned during training
RAG           = external retrieved knowledge
Tools         = controlled actions executed by Python
```

## First look inside an LLM

The current mental model is:

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

The embedding does **not** become the weights. The weights already exist inside the trained model and are used to process the numeric representations.

Next concept: attention and how the transformer uses context.
