---
name: zotero-rag
description: Answer thesis-related research questions by searching Sheen's Zotero library and synthesizing answers with verbatim quote-level citations. Use this skill whenever the user asks a question about prior literature, related work, theoretical background, or "what does paper X say about Y" — even if they don't explicitly mention Zotero, citations, or RAG. Especially trigger when the user is drafting thesis chapters, asking "what's the consensus on...", "find papers that discuss...", "support this claim from the literature", "use these specific papers to answer...", or pasting a sentence and asking for citations.
---

# zotero-rag

A local Consensus-style retrieval pipeline scoped to the user's Zotero library. Two-stage: a fast paper-level index over the entire library, plus on-demand chunk-level extraction for papers that actually get queried. No re-indexing required when the user changes scope — scope is per-query.

## When to use this skill

- "What do my papers say about morphological computation?"
- "Find me a citation for the claim that soft robots benefit from underactuation."
- "Use these three papers to answer my question about <topic>."
- "I'm writing this paragraph — back it up with sources from my library."

Do NOT use this skill for general world-knowledge questions, web lookups, or any question where the corpus the user cares about is not their Zotero library.

## Two-stage architecture

**Layer 1 — paper-level index (built once, refreshed cheaply):**
Every PDF-bearing item in the user's Zotero library is embedded by its title + abstract using SPECTER2. Tiny on disk, ~30 seconds to build for a few hundred papers, ~seconds to refresh after the user adds new papers (`--incremental`).

**Layer 2 — chunk-level cache (lazy, per-paper):**
A paper's PDF only gets parsed and chunk-embedded the first time it's actually included in a query result. The chunks are then persisted in the same ChromaDB and reused on subsequent queries. Net effect: papers the user never asks about never get parsed.

This means scope is dynamic. There's no "build the thesis index" step — there's just "the index" (whole library) plus "this query's scope" (whatever subset the user wants right now).

## Workflow

### Step 0 — Check that the index exists

Look at `vector_db_path` in `config.json`. If it contains `chroma.sqlite3` and the `papers` collection is non-empty, you're good. If not, instruct the user to run:

```bash
python scripts/index.py --config config.json
```

### Step 1 — Choose a scope

Three flavors, in order of preference depending on the user's request:

- **`--scope all`** (default): when the user is exploring or doesn't know which papers are relevant. "What do my papers say about X?" → use `all`.
- **`--scope collection:NAME`**: when the user references a Zotero collection. "What's in my Thesis folder about X?" → use `collection:Thesis`. The skill resolves this to citekeys via Zotero's sqlite, including all sub-collections.
- **`--scope citekey1,citekey2,...`**: when the user names specific papers, or when a previous turn already narrowed things down. "Use the Müller paper and the Rus paper to answer..." → look up their citekeys, pass them.

If the user's request is ambiguous about scope, prefer `all` for the first query and offer to narrow afterwards.

### Step 2 — Run the query

In Cowork (where Claude runs in a sandbox without the user's torch/SPECTER2 install), the workflow is **host-side execution + file bridge**:

1. Tell the user the exact PowerShell command to run on their machine:

   ```powershell
   python scripts/query.py --config config.json `
       --question "<the user's question>" `
       --scope <SCOPE>
   ```

2. The script writes JSON to `<vector_db_path>/../last_query.json` (default: `data/last_query.json`) AND prints to stdout.

3. After the user confirms the script finished, **Read the JSON file** at that path and proceed to Step 3.

If the result includes papers whose chunks haven't been cached yet, the script will pause to extract+embed them (~5-15 seconds per paper). This only happens once per paper, ever.

The JSON file looks like:

```json
{
  "question": "...",
  "scope": "all",
  "papers": [
    {"citekey": "mullerWhat...2017", "title": "...", "year": 2017, "score": 0.81}
  ],
  "passages": [
    {"citekey": "mullerWhat...2017", "section": "Abstract", "page": 1,
     "text": "verbatim text from the paper", "score": 0.79}
  ]
}
```

### Step 3 — Synthesize the answer with strict citations

Read the JSON. Then write the answer following these rules:

1. **Every factual claim must be backed by a passage in the JSON.** If the JSON doesn't support a claim, do not make the claim — say "the library doesn't cover this directly" instead of guessing.
2. **Quote, then cite.** After each claim, paste the supporting verbatim quote in quotation marks, then the citation in `[@citekey, p.X]` form.
3. **Group passages by paper** when summarizing — don't shuffle so badly that the reader can't trace a single paper's argument.
4. **Be honest about coverage.** If only 2 of the top 5 papers actually said something relevant, say so.

### Step 4 — Offer to refine scope

After answering, if the result is broad, offer the user a way to narrow: "These 5 papers came up — want me to dig deeper using just the Müller and Rus ones?" Then a follow-up query uses `--scope <those citekeys>`.

## Conversational scope patterns

Common patterns and how to handle them:

| User says | Scope to use |
|---|---|
| "What do my papers say about X?" | `--scope all` |
| "Search the Thesis collection for X" | `--scope collection:Thesis` |
| "Use these three papers to answer X" + names | look up citekeys, `--scope <list>` |
| "Use the same papers as last time but for question Y" | reuse the citekeys from the previous turn's result |
| "Add the Müller paper to the previous search" | union previous scope with the new citekey |

Track scope across turns as part of conversation context — don't make the user re-type citekeys every time.

## Refreshing the index

When the user mentions adding papers in Zotero, suggest:

```bash
python scripts/index.py --config config.json --incremental
```

This adds new papers to the paper-level index in seconds. Chunks are still lazy — they extract only when a new paper actually shows up in a query result.

## How citekeys are resolved

Two-tier strategy: BBT-style citekey from `references.bib` if matched by title; otherwise a provisional `<surname><FirstTitleWord><year>` key. If a citation in an answer uses a provisional key, that's a flag the paper isn't yet in `references.bib` — useful signal for the user.

## Why SPECTER2

SPECTER2 is AllenAI's encoder fine-tuned on scientific literature with a citation-prediction objective: papers cited near each other end up close in embedding space. That's exactly the relation we want for "find papers relevant to this thesis claim." Generic embeddings rank by surface similarity and can pull in tutorial blog posts; SPECTER2 ranks by citation-graph neighborhood.

## Files

- `SKILL.md` — this file
- `config.json` — paths only (zotero_root, references_bib, vector_db_path)
- `scripts/common.py` — shared library (Zotero reader, SPECTER2, chunk extraction)
- `scripts/index.py` — paper-level indexing
- `scripts/query.py` — scope-aware query with on-demand chunks
- `scripts/requirements.txt` — Python deps
- `README.md` — first-time setup walkthrough

## Failure modes

- **Image-only PDF**: skipped with warning. OCR with `ocrmypdf` and re-run.
- **Zotero sqlite locked**: handled — falls back to `.bak`.
- **Question outside corpus scope**: if all retrieval scores are below ~0.3, tell the user the library doesn't cover this rather than confabulating.
- **Citekey collision**: handled — second occurrence gets `_v2`, third `_v3`. If the user sees these, that's a hint the paper is duplicated in their Zotero library.
