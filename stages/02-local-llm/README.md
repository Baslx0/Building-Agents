# Stage 02 — Local LLM Integration

**Status: In Progress**

This stage connects Python to a local language model and builds the mental model needed before structured tool calling.

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
- understanding `system`, `user`, and `assistant`
- keeping conversation state in `chats_history`
- using `.append()` to add user and assistant messages
- sending the full conversation history back to the model
- wrapping chat behavior in a Python function
- using `while True` for continuous conversation
- using `break` for a clean exit
- understanding the difference between LLM knowledge, RAG, and tools

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

## LLM input pipeline

The current mental model is:

```text
User text
   ↓
Tokenizer
   ↓
Tokens
   ↓
Vocabulary lookup
   ↓
Token IDs
   ↓
LLM
   ↓
Embedding Matrix lookup
   ↓
Embeddings
   ↓
Transformer / Attention
```

Key ideas:

- The tokenizer is a preprocessing component associated with the model, not part of the transformer neural network itself.
- The tokenizer splits text into tokens and uses its vocabulary to map each token to a fixed Token ID.
- The vocabulary stores mappings such as `token → token ID`.
- Token IDs are identifiers only; they do not contain meaning by themselves.
- Inside the model, each Token ID is used as an index into the learned Embedding Matrix.
- The selected vector is the token's embedding.
- The Embedding Matrix is learned during model training.
- Embeddings are processed by transformer layers using learned weights.
- Attention is one of the mechanisms used to build context-aware representations.

## Tokenizer mental model

```text
Input text
   ↓
Tokenizer
   ├─ split text according to its tokenization algorithm
   ├─ use Vocabulary
   └─ map known token pieces to Token IDs
   ↓
[Token ID, Token ID, ...]
```

A useful simplification:

```text
Tokenizer = splitting + vocabulary lookup + Token ID output
Vocabulary = known token pieces + their fixed IDs
```

The exact split depends on the tokenizer algorithm and vocabulary; it is not simply linguistic understanding.

## LLM output pipeline

After the transformer processes the current context, the model predicts the next token:

```text
Processed context
      ↓
Logits
      ↓
Probabilities
      ↓
Choose next token
      ↓
Append token to context
      ↓
Repeat
```

The final answer is generated token by token.

## Scope decision

The internal LLM concepts above are enough for the current project goal.

This project is focused on **Custom Agents**, not training or implementing an LLM from scratch. Deep topics such as BPE internals, backpropagation, multi-head attention math, normalization, residual connections, and training loss are intentionally deferred.

## Next step

Return to agent building:

```text
Local LLM
   ↓
Structured decision
   ↓
Tool selection
   ↓
Argument validation
   ↓
Controlled Python execution
```

The next practical concept is **Structured Output** before real tool execution.
