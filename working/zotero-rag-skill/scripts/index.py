"""
Build / refresh the paper-level vector index from a Zotero library.

By default this indexes EVERY PDF-bearing item in your Zotero library —
just title + abstract, ~30 seconds for a few hundred papers. Chunks (full PDF
text) are NOT indexed here; query.py extracts them on demand the first time
a paper is actually queried.

Usage:
    python scripts/index.py --config config.json [options]

Options:
    --collections NAME [NAME ...]   only index these Zotero collections
                                    (default: entire library)
    --with-chunks                   also pre-extract chunks for every paper
                                    (slow — undoes the lazy-loading benefit;
                                    use only if you want all PDFs cached upfront)
    --incremental                   only embed papers not already indexed
    --dry-run                       resolve everything but skip embedding
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    Specter2, assign_citekeys, extract_chunks, fetch_papers,
    log, open_zotero_db, resolve_collections,
)


def index_corpus(config: dict, collections: list[str] | None,
                 with_chunks: bool, incremental: bool, dry_run: bool) -> None:
    zotero_root = Path(config["zotero_root"]).expanduser()
    db_path = Path(config["vector_db_path"]).expanduser()
    db_path.mkdir(parents=True, exist_ok=True)
    bib_path = (Path(config["references_bib"]).expanduser()
                if config.get("references_bib") else None)

    con = open_zotero_db(zotero_root)
    cids = resolve_collections(con, collections) if collections else None
    if cids is not None:
        log.info("scope = %d collection IDs from %s", len(cids), collections)
    else:
        log.info("scope = entire Zotero library")

    papers = fetch_papers(con, zotero_root, collection_ids=cids)
    log.info("found %d unique PDF-bearing papers in scope", len(papers))

    assign_citekeys(papers, bib_path)

    if dry_run:
        log.info("dry-run: stopping before embedding. Sample:")
        for p in papers[:8]:
            log.info("  %-50s %s", p.citekey[:48], p.title[:60])
        return

    import chromadb
    client = chromadb.PersistentClient(path=str(db_path))
    paper_col = client.get_or_create_collection("papers")
    chunk_col = client.get_or_create_collection("chunks")

    existing: set[str] = set()
    if incremental:
        try:
            existing = set(paper_col.get()["ids"])
            log.info("incremental: %d papers already indexed", len(existing))
        except Exception:
            pass

    encoder = Specter2()
    new_papers = [p for p in papers if p.citekey not in existing]

    if new_papers:
        log.info("encoding %d papers (title + abstract)...", len(new_papers))
        inputs = [f"{p.title} {encoder.tokenizer.sep_token} {p.abstract}".strip()
                  for p in new_papers]
        vecs = encoder.encode(inputs)
        paper_col.add(
            ids=[p.citekey for p in new_papers],
            embeddings=vecs,
            documents=[f"{p.title}\n\n{p.abstract}" for p in new_papers],
            metadatas=[{
                "citekey": p.citekey, "zotero_key": p.zotero_key,
                "title": p.title, "year": p.year or 0,
                "authors": ", ".join(p.authors[:3]),
            } for p in new_papers],
        )

    if with_chunks:
        log.info("--with-chunks: pre-extracting chunks for all papers (slow)...")
        for p in new_papers:
            chunks = extract_chunks(p, encoder.tokenizer)
            if not chunks:
                continue
            log.info("  %s: %d chunks", p.citekey[:40], len(chunks))
            cvecs = encoder.encode([c.text for c in chunks])
            chunk_col.add(
                ids=[f"{p.citekey}::c{i}" for i in range(len(chunks))],
                embeddings=cvecs,
                documents=[c.text for c in chunks],
                metadatas=[{
                    "citekey": c.citekey, "section": c.section, "page": c.page,
                    "title": p.title, "year": p.year or 0,
                } for c in chunks],
            )

    log.info("done. papers indexed: %d, chunks: %d",
             paper_col.count(), chunk_col.count())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--collections", nargs="+", default=None,
                    help="restrict to these Zotero collection names (default: whole library)")
    ap.add_argument("--with-chunks", action="store_true",
                    help="also pre-extract PDF chunks (defeats lazy loading)")
    ap.add_argument("--incremental", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    index_corpus(config, collections=args.collections,
                 with_chunks=args.with_chunks,
                 incremental=args.incremental, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
