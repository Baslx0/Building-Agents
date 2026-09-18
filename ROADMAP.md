# Roadmap

The repository is organized around **meaningful stages**, not individual exercises. A stage can contain several Python and agent concepts; its code represents the best checkpoint reached at the end of that stage.

## Stage 01 — Rule-Based Foundation

**Status: Complete**

This stage groups everything required to build the first controlled tool system:

- functions and parameters
- f-strings
- `print()` vs `return`
- early returns
- modules, functions, methods, and attributes
- `subprocess.run()`
- stdout, stderr, and return codes
- first real IT tool: `ping_host(host)`
- second tool: `greet(name)`
- manual routing
- command parsing with `.split()`
- list indexes and `len()`
- basic input validation
- controlled unsupported-tool responses

End-of-stage checkpoint: `stages/01-rule-based-foundation/agent.py`.

The important limitation is intentional: tool selection is still encoded with Python rules.

## Stage 02 — Local LLM

**Status: Next**

Give the system a language-understanding layer without jumping to a hosted API or agent framework.

Goals:
- choose a small model suitable for local inference
- run the model locally
- call it from Python
- understand prompts, responses, and the local inference boundary
- ask it to identify intent without allowing it to execute system commands

End goal: natural language can be converted into a proposed action.

## Stage 03 — Structured Tool Calling

Turn the model's proposed action into a controlled interface.

Goals:
- define a tool registry
- describe allowed tools and arguments
- request structured decisions
- parse and validate model output
- reject unknown tools or malformed arguments
- execute exactly one approved Python tool

Conceptual decision:

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

Add bounded iterations so the agent cannot loop forever.

## Stage 05 — State, Memory & Guardrails

Learn and implement only the state the agent needs.

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

Grow the learning project into a useful IT support / operations agent.

Candidate diagnostic tools include:
- DNS lookup
- HTTP/HTTPS reachability
- network information
- system information
- service checks

Tools should stay explicit, bounded, and testable.

## Stage 07 — Local vs Cloud API

After the architecture is understood locally, abstract or swap the inference layer and compare it with a hosted LLM API.

The core controller, validation, and tools should remain largely unchanged.
