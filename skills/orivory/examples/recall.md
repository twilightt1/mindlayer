# Example: "Recall past decisions"

User: *"What did we decide about the vector store last week?"*

## What the agent does

1. `search_memory` with the user's own words: `query: "vector store decision"`
   (not a paraphrase, not "pgvector" — that presumes the answer).
2. If a hit looks right → `get_memory` for the full content before quoting.
3. Answer with the title cited: "Per *Decision: hub vector store → pgvector*,
   you chose pgvector over ChromaDB, starting next sprint."

## Anti-patterns

- Don't answer from general knowledge if the search is empty — say "I don't
  recall that in your memories" and offer to save the decision now.
- Don't quote a memory's full content without `get_memory` — `search_memory`
  returns content previews.
- Don't guess the date: the memory's `captured_at` is in the result.

## Follow-ups that make the memory better

If the user corrects the answer ("we switched back last month"), that's a
`add_memory` (the update) + `forget_memory` of the stale decision — Orivory's
salience loop will surface the new one from then on.
