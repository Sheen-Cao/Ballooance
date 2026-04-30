# zotero-rag — local Consensus-style RAG over your Zotero library

Two-stage retrieval over your own corpus: a fast paper-level index over the entire library, plus on-demand chunk extraction for papers that actually get queried. No re-indexing when you change scope — scope is per-query.

## Setup (one-time)

### 1. Install Python dependencies

From this directory:

```powershell
pip install -r scripts/requirements.txt
```

First run also downloads SPECTER2 (~500 MB), one-time.

### 2. Confirm `config.json`

Three paths only — no collection list needed anymore:

```json
{
  "zotero_root": "C:/Users/Sheen/Zotero",
  "references_bib": "D:/Share/CMU/Thesis/Ballooance/references.bib",
  "vector_db_path": "D:/Share/CMU/Thesis/Ballooance/working/zotero-rag-skill/data/chroma"
}
```

### 3. Build the paper-level index (entire library by default)

```powershell
python scripts/index.py --config config.json
```

~30 seconds for a few hundred papers. This embeds every PDF-bearing item in your Zotero library by its title + abstract. PDF chunking is deferred — see "How it works" below.

If you want to restrict the initial index to one or more Zotero collections, use `--collections`:

```powershell
python scripts/index.py --config config.json --collections Thesis "Robotic Embodiment"
```

But there's usually no reason to — the whole library only takes a few seconds longer and gives you full search coverage from any future query.

### 4. After adding papers in Zotero

```powershell
python scripts/index.py --config config.json --incremental
```

Adds new papers to the paper-level index in seconds. Chunks are still lazy.

## Using the skill

In Cowork, just ask Claude things like:

- "What do my papers say about morphological computation?" — searches the whole library
- "Find me a citation for [claim]" — likewise
- "Use the Müller and Rus papers to answer [question]" — Claude scopes to those specific citekeys
- "Search the Thesis collection for [topic]" — scopes to that Zotero collection

The first time a paper appears in any query result, its PDF gets parsed and chunk-embedded (~5-15 sec). After that the chunks are cached and reused.

## How it works (one paragraph)

`index.py` reads your Zotero `zotero.sqlite` directly (or its `.bak` if Zotero is running), pulls every PDF-bearing item, and embeds each one's title + abstract with SPECTER2 — fast because it's only one vector per paper. `query.py` embeds your question with the same model, retrieves the top-N most relevant papers (optionally restricted by `--scope`), and then for any paper in that result whose chunks aren't yet in the cache, it opens the PDF, splits the text into ~400-token section-aware chunks, embeds them, and stores them in ChromaDB. Then it does a chunk-level search restricted to those papers and returns the top passages. Net effect: one paper-level index of the whole library plus a chunk-level cache that grows organically as you actually use papers.

## Manual query

```powershell
python scripts/query.py --config config.json `
    --question "your question" `
    --scope all `
    --top-papers 5 --top-chunks 12
```

`--scope` can be:
- `all` (default)
- `collection:CollectionName` (resolves via Zotero, includes sub-collections)
- `citekey1,citekey2,...` (specific papers only)

## Limitations

- Image-only PDFs are skipped (run `ocrmypdf` first if needed).
- SPECTER2 is trained on English scientific abstracts; non-English papers work but with degraded retrieval quality.
- Page numbers are PDF page numbers, not paper page numbers — fine for going back to the source, cite carefully when writing.
- The skill answers only from what's in your library; if a topic isn't covered, it should say so rather than guessing.
