# Roadmap

This roadmap follows the actual learning order rather than jumping directly to an agent framework.

## Phase 01 — Functions to Tools

**Status:** Complete

Learned:
- function parameters
- dynamic values and f-strings
- `print()` vs `return`
- early returns

Outcome: functions can receive inputs and return reusable results.

## Phase 02 — First Real IT Tool

**Status:** Complete

Introduced Python's `subprocess` module and Windows ping.

Learned:
- `module.function()`
- object attributes such as `result.stdout`
- `capture_output=True`
- `text=True`
- process return codes

Outcome: `ping_host(host)` performs a real system operation and returns a simple reachable/unreachable result.

## Phase 03 — Manual Tool Router

**Status:** Complete

Added a second tool, `greet(name)`, then built a CLI router.

Learned:
- choosing between tools
- passing arguments dynamically
- avoiding duplicate tool execution
- separating execution from display
- why `print()` can accidentally produce `None` at the caller

Outcome: one program can expose multiple tools and select one at runtime.

## Phase 04 — Command Parser and Validation

**Status:** Current checkpoint

Moved from numeric menu choices toward commands such as:

```text
ping google.com
greet Basil
```

Learned:
- `.split()`
- list indexes
- `len()`
- `and` / `or`
- validation before accessing arguments
- reducing unnecessary nesting with early returns

Limitation: the router only understands syntax explicitly programmed into Python.

## Phase 05 — Give the Agent a Brain

**Status:** Next

Run a small local LLM suitable for local inference.

First goal: send a simple prompt from Python and receive a response. No tool calling yet.

Then teach the model about the available tools and request a structured decision, conceptually:

```json
{
  "tool": "ping_host",
  "arguments": {
    "host": "google.com"
  }
}
```

The Python controller—not the model—will validate that decision.

## Phase 06 — Tool Registry

Represent available tools in a controlled registry instead of hard-coded routing branches.

Goals:
- map tool names to Python functions
- define expected arguments
- reject unknown tools
- reject malformed arguments

## Phase 07 — Tool Calling

Connect model decisions to the registry.

Flow:

```text
Natural language
    -> local LLM
    -> structured tool request
    -> validation
    -> Python tool execution
    -> tool result
```

## Phase 08 — Agent Loop

Return tool results to the model so it can formulate the final answer and, where appropriate, decide whether another safe tool call is required.

Add a strict maximum iteration count.

## Phase 09 — Memory and State

Learn the difference between:
- conversation history
- temporary runtime state
- persistent memory

Add only the state that the IT agent actually needs.

## Phase 10 — Practical IT Agent

Expand the toolset gradually. Candidate read-only/diagnostic tools:

- DNS lookup
- HTTP/HTTPS reachability check
- local network information
- system information
- service checks

Each tool should have explicit inputs, predictable outputs, validation, and bounded permissions.

## Phase 11 — Cloud API Comparison

Swap or abstract the model layer and compare the local implementation with a hosted LLM API.

The controller and tools should remain largely unchanged.
