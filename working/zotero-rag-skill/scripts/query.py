"""
Query the local SPECTER2/ChromaDB index, with dynamic scope and on-demand
chunk extraction.

Usage:
    python scripts/query.py --config config.json \
        --question "your question here" \
        [--scope SCOPE] \
        [--top-papers 5] [--top-chunks 12]

SCOPE values:
    all                                (default — search the whole indexed library)
    citekey1,citekey2,citekey3         (just these papers)
    collection:Thesis                  (papers in the Zotero collection "Thesis"
                                       and all its sub-collections)

Stdout: a single JSON document with keys {question, scope, papers, passages}.

The first time a paper is included in any scope, its PDF gets parsed, split
into chunks, and embedded — about 5-15 seconds per paper. After that the
chunks are cached in the same ChromaDB and reused instantly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    Specter2, assign_citekeys, extract_chunks, fetch_papers, log,
    open_zotero_db, resolve_collections,
)


def resolve_scope(scope: str, config: dict) -> list[str] | None:
    """Return list of citekeys to restrict to, or None for 'all'."""
    if scope == "all" or not scope:
        return None
    if scope.startswith("collection:"):
        coll_name = scope[len("collection:"):]
        zotero_root = Path(config["zotero_root"]).expanduser()
        bib_path = (Path(config["references_bib"]).expanduser()
                    if config.get("references_bib") else None)
        con = open_zotero_db(zotero_root)
        cids = resolve_collections(con, [coll_name])
        if not cids:
            log.warning("collection %r resolved to no IDs", coll_name)
            return []
        papers = fetch_papers(con, zotero_root, collection_ids=cids)
        assign_citekeys(papers, bib_path)
        return [p.citekey for p in papers]
    # comma-separated citekey list
    return [s.strip() for s in scope.split(",") if s.strip()]


def ensure_chunks_cached(
    citekeys: list[str], chunk_col, paper_col, config: dict, encoder: Specter2,
) -> None:
    """For each citekey, check if chunks exist; if not, extract+embed and cache."""
    if not citekeys:
        return
    have = chunk_col.get(where={"citekey": {"$in": citekeys}}, include=[])
    have_keys = {m_id.split("::")[0] for m_id in have["ids"]}
    missing = [ck for ck in citekeys if ck not in have_keys]
    if not missing:
        return
    log.info("on-demand chunk extraction for %d paper(s)...", len(missing))

    # Look up Zotero metadata for missing citekeys via paper_col, then re-fetch
    # PDF paths from Zotero so extract_chunks() can run.
    paper_meta = paper_col.get(ids=missing, include=["metadatas"])
    zotero_keys_by_citekey = {
        m["citekey"]: m["zotero_key"]
        for m in paper_meta["metadatas"]
    }

    zotero_root = Path(config["zotero_root"]).expanduser()
    bib_path = (Path(config["references_bib"]).expanduser()
                if config.get("references_bib") else None)
    con = open_zotero_db(zotero_root)
    all_papers = fetch_papers(con, zotero_root, collection_ids=None)
    assign_citekeys(all_papers, bib_path)
    by_citekey = {p.citekey: p for p in all_papers}

    for ck in missing:
        paper = by_citekey.get(ck)
        if not paper:
            log.warning("citekey %s in index but no Zotero match — skipping", ck)
            continue
        chunks = extract_chunks(paper, encoder.tokenizer)
        if not chunks:
            continue
        log.info("  %s: %d chunks", ck[:40], len(chunks))
        vecs = encoder.encode([c.text for c in chunks])
        chunk_col.add(
            ids=[f"{ck}::c{i}" for i in range(len(chunks))],
            embeddings=vecs,
            documents=[c.text for c in chunks],
            metadatas=[{
                "citekey": c.citekey, "section": c.section, "page": c.page,
                "title": paper.title, "year": paper.year or 0,
            } for c in chunks],
        )


def query(config: dict, question: str, scope: str,
          top_papers: int, top_chunks: int) -> dict:
    import chromadb

    db_path = Path(config["vector_db_path"]).expanduser()
    client = chromadb.PersistentClient(path=str(db_path))
    paper_col = client.get_collection("papers")
    chunk_col = client.get_or_create_collection("chunks")

    encoder = Specter2()
    qvec = encoder.encode([question])[0]

    # Stage 1: paper-level retrieval, optionally scoped
    scope_keys = resolve_scope(scope, config)
    paper_kwargs = {
        "query_embeddings": [qvec],
        "n_results": top_papers,
        "include": ["metadatas", "distances"],
    }
    if scope_keys is not None:
        if not scope_keys:
            return {"question": question, "scope": scope,
                    "papers": [], "passages": [],
                    "note": "scope resolved to no papers"}
        paper_kwargs["where"] = {"citekey": {"$in": scope_keys}}
        # if scope is small, ask for everything in scope
        if len(scope_keys) <= top_papers:
            paper_kwargs["n_results"] = len(scope_keys)

    paper_hits = paper_col.query(**paper_kwargs)
    paper_meta = paper_hits["metadatas"][0]
    paper_dist = paper_hits["distances"][0]
    relevant_ck = [m["citekey"] for m in paper_meta]

    papers_out = [{
        "citekey": m["citekey"], "title": m["title"],
        "year": m.get("year"), "authors": m.get("authors"),
        "score": round(1.0 - d, 4),
    } for m, d in zip(paper_meta, paper_dist)]

    # Stage 2: ensure chunks for the top papers are cached, then retrieve
    ensure_chunks_cached(relevant_ck, chunk_col, paper_col, config, encoder)

    chunk_hits = chunk_col.query(
        query_embeddings=[qvec], n_results=top_chunks,
        where={"citekey": {"$in": relevant_ck}},
        include=["documents", "metadatas", "distances"],
    )
    passages_out = []
    if chunk_hits["ids"] and chunk_hits["ids"][0]:
        for doc, meta, dist in zip(
            chunk_hits["documents"][0],
            chunk_hits["metadatas"][0],
            chunk_hits["distances"][0],
        ):
            passages_out.append({
                "citekey": meta["citekey"], "title": meta.get("title"),
                "section": meta.get("section"), "page": meta.get("page"),
                "text": doc, "score": round(1.0 - dist, 4),
            })

    return {"question": question, "scope": scope,
            "papers": papers_out, "passages": passages_out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--question", required=True)
    ap.add_argument("--scope", default="all",
                    help='"all" | "citekey1,citekey2,..." | "collection:NAME"')
    ap.add_argument("--top-papers", type=int, default=5)
    ap.add_argument("--top-chunks", type=int, default=12)
    ap.add_argument("--out", type=Path, default=None,
                    help="JSON output path. Default: <vector_db_path>/../last_query.json")
    ap.add_argument("--no-stdout", action="store_true",
                    help="suppress JSON on stdout (only write to --out file)")
    args = ap.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = query(config, args.question, args.scope,
                   args.top_papers, args.top_chunks)

    # Always also write to a stable file so Claude can Read it
    # without the user piping shell output around.
    out_path = args.out or (
        Path(config["vector_db_path"]).expanduser().parent / "last_query.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    log.info("wrote %s", out_path)

    if not args.no_stdout:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
