# Example: "Remember this"

User: *"Remember that we decided to use pgvector for the hub's vector store,
replacing ChromaDB, starting next sprint."*

## What the agent does

1. `add_memory`:
   - `title`: "Decision: hub vector store → pgvector (next sprint)"
   - `content`: "We decided to replace ChromaDB with pgvector as the hub's
     vector store, effective next sprint. (Decided in conversation, 2026-09-04.)"
   - `tags`: ["decisions", "infra"]

## Why this shape

- **Title is the searchable handle** — next month "what did we decide about
  the vector store?" must hit it.
- **Content carries the decision, the context, and the date** — a bare
  "pgvector" is useless in a year.
- One decision per memory: the migration *plan* would be a second memory.

## What the agent says

"Saved: *Decision: hub vector store → pgvector (next sprint)*. It'll show up
when you ask about the vector store or infra decisions."
