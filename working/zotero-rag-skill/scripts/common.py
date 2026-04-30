"""Shared logic for the zotero-rag skill.

Imported by both index.py (paper-level indexing) and query.py (retrieval +
on-demand chunk extraction).
"""

from __future__ import annotations

import logging
import re
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("zotero-rag")

SPECTER2_BASE = "allenai/specter2_base"
SPECTER2_ADAPTER = "allenai/specter2"
TARGET_TOKENS_PER_CHUNK = 400
MAX_TOKENS = 512


# ------------------------------------------------------------------ #
# Data model
# ------------------------------------------------------------------ #
@dataclass
class Paper:
    citekey: str
    zotero_key: str
    title: str
    abstract: str
    year: int | None
    authors: list[str]
    pdf_path: Path | None


@dataclass
class Chunk:
    citekey: str
    section: str
    page: int
    text: str


# ------------------------------------------------------------------ #
# Zotero sqlite reader
# ------------------------------------------------------------------ #
def open_zotero_db(zotero_root: Path) -> sqlite3.Connection:
    candidates = [zotero_root / "zotero.sqlite", zotero_root / "zotero.sqlite.bak"]
    last_err: Exception | None = None
    for cand in candidates:
        if not cand.exists():
            continue
        try:
            tmp_db = Path(tempfile.mkdtemp(prefix="zotero_rag_")) / "zotero.sqlite"
            shutil.copy2(cand, tmp_db)
            con = sqlite3.connect(str(tmp_db))
            con.execute("SELECT COUNT(*) FROM items").fetchone()
            log.info("opened Zotero DB via copy of %s", cand.name)
            return con
        except Exception as exc:
            last_err = exc
            log.warning("could not open %s: %s", cand.name, exc)
    raise RuntimeError(f"could not open any Zotero DB under {zotero_root}: {last_err}")


def resolve_collections(con: sqlite3.Connection, names: list[str]) -> set[int]:
    cur = con.cursor()
    roots: list[int] = []
    for nm in names:
        rows = cur.execute(
            "SELECT collectionID FROM collections WHERE collectionName=?", (nm,)
        ).fetchall()
        if not rows:
            log.warning("collection %r not found", nm)
            continue
        roots.extend(r[0] for r in rows)
    out: set[int] = set()
    stack = list(roots)
    while stack:
        cid = stack.pop()
        if cid in out:
            continue
        out.add(cid)
        children = cur.execute(
            "SELECT collectionID FROM collections WHERE parentCollectionID=?", (cid,)
        ).fetchall()
        stack.extend(c[0] for c in children)
    return out


def _field(cur, item_id: int, name: str) -> str:
    row = cur.execute(
        """SELECT idv.value FROM itemDataValues idv
           JOIN itemData id ON id.valueID=idv.valueID
           JOIN fields f ON f.fieldID=id.fieldID
           WHERE id.itemID=? AND f.fieldName=?""",
        (item_id, name),
    ).fetchone()
    return row[0] if row else ""


def _authors(cur, item_id: int) -> list[str]:
    rows = cur.execute(
        """SELECT c.lastName FROM itemCreators ic
           JOIN creators c ON c.creatorID=ic.creatorID
           WHERE ic.itemID=? ORDER BY ic.orderIndex""",
        (item_id,),
    ).fetchall()
    return [r[0] for r in rows if r[0]]


def fetch_papers(
    con: sqlite3.Connection,
    zotero_root: Path,
    collection_ids: set[int] | None = None,
) -> list[Paper]:
    """Fetch papers from Zotero. If collection_ids is None, fetch ALL PDF-bearing
    items in the entire library. Otherwise filter to those collections.
    """
    cur = con.cursor()
    if collection_ids is not None:
        ph = ",".join("?" * len(collection_ids))
        rows = cur.execute(
            f"""SELECT DISTINCT i.itemID, i.key, att_data.path, att_item.key
                FROM collectionItems ci
                JOIN items i ON i.itemID=ci.itemID
                JOIN itemAttachments att_data ON att_data.parentItemID=i.itemID
                JOIN items att_item ON att_item.itemID=att_data.itemID
                WHERE ci.collectionID IN ({ph})
                  AND att_data.contentType='application/pdf'""",
            tuple(collection_ids),
        ).fetchall()
    else:
        rows = cur.execute(
            """SELECT DISTINCT i.itemID, i.key, att_data.path, att_item.key
               FROM items i
               JOIN itemAttachments att_data ON att_data.parentItemID=i.itemID
               JOIN items att_item ON att_item.itemID=att_data.itemID
               WHERE att_data.contentType='application/pdf'"""
        ).fetchall()

    seen: set[str] = set()
    papers: list[Paper] = []
    for item_id, paper_key, raw_path, att_key in rows:
        if paper_key in seen:
            continue
        pdf_path = _resolve_pdf_path(raw_path, att_key, zotero_root)
        if pdf_path is None:
            continue
        seen.add(paper_key)
        title = _field(cur, item_id, "title").strip()
        abstract = _field(cur, item_id, "abstractNote").strip()
        date = _field(cur, item_id, "date").strip()
        ymatch = re.search(r"(19|20)\d{2}", date)
        year = int(ymatch.group(0)) if ymatch else None
        authors = _authors(cur, item_id)
        papers.append(Paper(
            citekey=_provisional_citekey(authors, year, title),
            zotero_key=paper_key, title=title, abstract=abstract,
            year=year, authors=authors, pdf_path=pdf_path,
        ))
    return papers


def _resolve_pdf_path(raw, att_key, zotero_root) -> Path | None:
    if not raw:
        return None
    if raw.startswith("storage:"):
        p = zotero_root / "storage" / att_key / raw[len("storage:"):]
        return p if p.exists() else None
    p = Path(raw)
    return p if p.exists() else None


# ------------------------------------------------------------------ #
# Citekeys
# ------------------------------------------------------------------ #
def _normalize_title(s: str) -> str:
    s = re.sub(r"[{}]", "", s).lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def load_citekey_map(bib_path: Path | None) -> dict[str, str]:
    if not bib_path or not bib_path.exists():
        return {}
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, str] = {}
    for m in re.finditer(r"@\w+\{([^,]+),", text):
        ck = m.group(1).strip()
        chunk = text[m.start():m.start() + 3000]
        tm = re.search(r"title\s*=\s*[{\"](.+?)[}\"]\s*,", chunk, re.DOTALL)
        if tm:
            out[_normalize_title(tm.group(1))] = ck
    log.info("loaded %d citekeys from %s", len(out), bib_path.name)
    return out


def _provisional_citekey(authors: list[str], year: int | None, title: str) -> str:
    surname = re.sub(r"[^a-z]", "", (authors[0] if authors else "anon").lower()) or "anon"
    yr = str(year) if year else "nodate"
    tw = re.sub(r"[^A-Za-z]+", " ", title).strip().split()
    tw = (tw[0].lower() if tw else "untitled")[:12]
    return f"{surname}{tw.capitalize()}{yr}"


def assign_citekeys(papers: list[Paper], bib_path: Path | None) -> None:
    """Assign BBT citekeys where possible, then DROP duplicate papers (same
    normalized title = same paper, even if user added it to Zotero twice).
    Mutates `papers` in place.
    """
    # Pass 1: dedupe by normalized title — handles the common case of the same
    # paper added to Zotero multiple times (different items, same PDF/title).
    seen_titles: set[str] = set()
    kept: list[Paper] = []
    dropped = 0
    for p in papers:
        nt = _normalize_title(p.title)
        if not nt or nt in seen_titles:
            dropped += 1
            if nt:
                log.warning("dropping duplicate of %r (Zotero key %s)", p.title[:60], p.zotero_key)
            continue
        seen_titles.add(nt)
        kept.append(p)
    if dropped:
        log.info("dropped %d duplicate paper(s) with shared titles", dropped)
    papers[:] = kept

    # Pass 2: BBT citekey assignment via title match.
    citekey_map = load_citekey_map(bib_path)
    matched = 0
    for p in papers:
        norm = _normalize_title(p.title)
        if norm in citekey_map:
            p.citekey = citekey_map[norm]
            matched += 1
    log.info("matched %d/%d papers to BBT citekeys", matched, len(papers))

    # Pass 3: defense in depth for fallback-citekey collisions (rare now that
    # title-duplicates are gone, but possible if two genuinely different papers
    # share author + year + first title word).
    seen_ck: dict[str, int] = {}
    for p in papers:
        if p.citekey in seen_ck:
            seen_ck[p.citekey] += 1
            new = f"{p.citekey}_v{seen_ck[p.citekey]}"
            log.warning("citekey collision (different titles): %s -> %s (%s)",
                        p.citekey, new, p.title[:50])
            p.citekey = new
        else:
            seen_ck[p.citekey] = 1


# ------------------------------------------------------------------ #
# PDF -> chunks
# ------------------------------------------------------------------ #
SECTION_RE = re.compile(
    r"^\s*(\d{1,2}\.?\s+)?(abstract|introduction|background|related work|"
    r"methods?|methodology|results?|discussion|conclusion|references|appendix)\b",
    re.IGNORECASE,
)


def extract_chunks(paper: Paper, tokenizer) -> list[Chunk]:
    import fitz
    if not paper.pdf_path or not paper.pdf_path.exists():
        log.warning("no PDF for %s", paper.citekey)
        return []
    try:
        doc = fitz.open(paper.pdf_path)
    except Exception as exc:
        log.warning("could not open %s: %s", paper.pdf_path, exc)
        return []

    chunks: list[Chunk] = []
    section = "Body"
    buf: list[str] = []
    btok = 0
    bpage = 1

    def flush(page):
        nonlocal buf, btok
        if not buf:
            return
        text = " ".join(buf).strip()
        if len(text) > 50:
            chunks.append(Chunk(paper.citekey, section, bpage, text))
        buf = []
        btok = 0

    for pi, page in enumerate(doc, start=1):
        for line in (page.get_text("text") or "").splitlines():
            line = line.strip()
            if not line:
                continue
            m = SECTION_RE.match(line)
            if m:
                flush(pi)
                section = m.group(2).title()
                bpage = pi
                continue
            tlen = len(tokenizer.tokenize(line))
            if btok + tlen > TARGET_TOKENS_PER_CHUNK and buf:
                flush(pi)
                bpage = pi
            buf.append(line)
            btok += tlen
        if btok > TARGET_TOKENS_PER_CHUNK * 0.6:
            flush(pi)
            bpage = pi + 1

    flush(len(doc))
    doc.close()
    return chunks


# ------------------------------------------------------------------ #
# SPECTER2
# ------------------------------------------------------------------ #
class Specter2:
    def __init__(self) -> None:
        import torch
        from adapters import AutoAdapterModel
        from transformers import AutoTokenizer
        log.info("loading SPECTER2...")
        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(SPECTER2_BASE)
        self.model = AutoAdapterModel.from_pretrained(SPECTER2_BASE)
        self.model.load_adapter(SPECTER2_ADAPTER, source="hf",
                                load_as="proximity", set_active=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device).eval()
        log.info("SPECTER2 ready on %s", self.device)

    def encode(self, texts: Iterable[str], batch_size: int = 8) -> list[list[float]]:
        out: list[list[float]] = []
        batch: list[str] = []
        for t in texts:
            batch.append(t)
            if len(batch) == batch_size:
                out.extend(self._enc(batch))
                batch = []
        if batch:
            out.extend(self._enc(batch))
        return out

    def _enc(self, batch):
        enc = self.tokenizer(batch, padding=True, truncation=True,
                             return_tensors="pt", max_length=MAX_TOKENS).to(self.device)
        with self._torch.no_grad():
            out = self.model(**enc)
        return out.last_hidden_state[:, 0, :].cpu().tolist()
