# Roadmap

The repository is organized around **meaningful stages**, not individual exercises.

## Stage 01 — Rule-Based Foundation

**Status: Complete**

Covered Python functions, return values, subprocess, simple tools, parsing, routing, and input validation.

Checkpoint: `stages/01-rule-based-foundation/agent.py`.

## Stage 02 — Local LLM Integration

**Status: In Progress**

Current stack:

```text
Python → Ollama → Phi-4-mini
```

Completed so far:
- run a local model
- call it from Python
- use `system`, `user`, and `assistant` messages
- understand that Ollama provides the runtime/API while Phi-4-mini is the model
- keep conversation state in `chats_history`
- send the full history back to the model
- build a continuous `while True` chat loop
- understand the difference between LLM knowledge, RAG, and tools
- understand the input path from text → tokenizer → vocabulary → Token IDs → embeddings
- understand the role of the learned Embedding Matrix
- understand attention at a high level
- understand next-token generation through logits → probabilities → token selection

Internal LLM study stops here for now because the project goal is custom agent engineering, not LLM implementation.

Next:
- structured output
- controlled tool decisions
- argument validation
- tool execution

Checkpoint: `stages/02-local-llm/chat.py`.

## Stage 03 — Structured Tool Calling

Goals:
- define a tool registry
- describe allowed tools and arguments
- request structured decisions
- parse and validate model output
- reject unknown tools or malformed arguments
- execute exactly one approved Python tool

Example:

```json
{
  "tool": "ping_host",
  "arguments": {
    "host": "google.com"
  }
}
```

## Stage 04 — Agent Loop

Connect reasoning, execution, and results.

```text
User request
  -> model decision
  -> validation
  -> tool execution
  -> tool result
  -> model
  -> final response
```

## Stage 05 — State, Memory & Guardrails

Topics:
- conversation history
- runtime state
- persistent memory
- tool permissions
- argument validation
- timeouts and failures
- maximum iterations
- safe handling of side-effecting tools

## Stage 06 — Practical IT Agent

Candidate diagnostic tools:
- DNS lookup
- HTTP/HTTPS reachability
- network information
- system information
- service checks

## Stage 07 — Local vs Cloud API

Compare the local inference layer with a hosted LLM API while keeping the controller, validation, and tools as stable as possible.
