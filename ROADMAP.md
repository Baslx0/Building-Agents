# Roadmap

The repository is organized around **meaningful stages**, not individual exercises.

## Stage 01 — Rule-Based Foundation

**Status: Complete**

Covered Python functions, return values, subprocess, simple tools, parsing, routing, and input validation.

Checkpoint: `stages/01-rule-based-foundation/agent.py`.

## Stage 02 — Local LLM Integration

**Status: Complete**

Covered:
- local inference with Ollama + Phi-4-mini
- `system`, `user`, and `assistant` messages
- conversation state in `chats_history`
- a continuous chat loop
- the difference between LLM knowledge, RAG, and tools
- the high-level path from tokenizer → Token IDs → embeddings → transformer/attention
- next-token generation through logits and probabilities

Checkpoint: `stages/02-local-llm/chat.py`.

## Stage 03 — Structured Tool Calling

**Status: In Progress**

Completed so far:
- instruct the LLM to return JSON only
- use Ollama `format="json"`
- convert the returned JSON string with `json.loads()`
- extract the selected tool and arguments
- validate `ping_host` and the required `host` argument
- execute the real `ping_host(host)` function only after validation

Current flow:

```text
User request
  -> Phi-4-mini
  -> JSON decision
  -> Python dict
  -> validation
  -> ping_host(host)
  -> real result
```

Next:
- improve malformed/unsupported decision handling
- define a proper tool registry
- add another bounded tool
- return tool results to the model
- move toward a full agent loop

Checkpoint: `stages/03-structured-tool-calling/ping_agent.py`.

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
