"""検索用の索引を作る: DB の行・表を「チャンク」にして埋め込み、ベクトルを保存する。

usage: uv run --group rag python src/build_index.py [--db db/interface_spec.sqlite] [--embedder ruri-v3-310m]
  前提: build_db.py を実行済み（DB を作り直したら、これも実行し直す）
出力:
  DB の chunks テーブル     チャンク（行ごと・表ごと）の本文とメタ情報
  db/vectors.{embedder}.npy  chunks の chunk_id 順のベクトル（L2 正規化済み）
  db/embed_cache.{embedder}.npz  本文の sha256 → ベクトル。変わったチャンクだけ埋め込み直す
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm.embedding import get_embedder  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = {"kaigo": "介護保険", "shogai": "障害福祉"}


def header(r) -> list[str]:
    ex = f"（交換情報識別番号 {r['record_exchange_id']}）" if r["record_exchange_id"] else ""
    out = [f"{DOMAIN.get(r['domain'], r['domain'])} インタフェース仕様書 {r['volume']} {r['edition']}"]
    if r["section_name"]:
        out.append(f"節: {r['section_no'] or ''} {r['section_name']}")
    out.append(f"表: {r['title'] or '（表題なし）'}{ex}")
    return out


def build_chunks(con: sqlite3.Connection) -> list[dict]:
    con.row_factory = sqlite3.Row
    tables = {r["table_id"]: r for r in con.execute(
        "SELECT t.*, d.domain, d.volume, d.edition FROM spec_tables t JOIN documents d USING (doc_id)")}
    vals = defaultdict(list)
    for r in con.execute("SELECT item_id, kind, column_name, value FROM item_values"):
        vals[r["item_id"]].append(f"{r['column_name']}={r['value']}")
    notes = defaultdict(list)
    for r in con.execute("SELECT item_id, mark, text FROM item_notes WHERE text IS NOT NULL"):
        notes[r["item_id"]].append(f"{r['mark']} {r['text']}")
    names = defaultdict(list)
    chunks = []
    for it in con.execute("SELECT * FROM items ORDER BY item_id"):
        t = tables[it["table_id"]]
        names[it["table_id"]].append(it["name_full"] or "")
        spec = " / ".join(x for x in [f"属性 {it['type']}" if it["type"] else "",
                                      f"桁数 {it['length_raw'] or it['length']}" if (it["length_raw"] or it["length"]) else "",
                                      f"必須 {it['required']}" if it["required"] else ""] if x)
        lines = header(t) + [f"項番 {it['no_raw'] or it['no'] or '-'}: {it['name_full'] or '（項目名なし）'}"]
        if spec:
            lines.append(spec)
        for label, key in (("内容", "content"), ("備考", "note")):
            if it[key]:
                lines.append(f"{label}: {it[key]}")
        if vals[it["item_id"]]:
            lines.append("列: " + " ".join(vals[it["item_id"]]))
        if notes[it["item_id"]]:
            lines.append("注記: " + " ".join(notes[it["item_id"]]))
        chunks.append({"kind": "item", "item_id": it["item_id"], "table_id": it["table_id"], "text": "\n".join(lines)})
    # 表ごとのチャンク（「J611 の基本情報レコードの項目は？」のような表単位の質問用）
    for tid, t in tables.items():
        cols = json.loads(t["columns"] or "[]")
        lines = header(t) + [f"表の種類: {t['table_kind']}", f"PDF {t['page_from']}〜{t['page_to']}ページ"]
        if cols:
            lines.append("列: " + " | ".join(cols))
        lines.append("項目: " + "、".join(n for n in names[tid] if n)[:1500])
        chunks.append({"kind": "table", "item_id": None, "table_id": tid, "text": "\n".join(lines)})
    for c in chunks:
        c["sha"] = hashlib.sha256(c["text"].encode("utf-8")).hexdigest()
    return chunks


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="db/interface_spec.sqlite")
    ap.add_argument("--embedder", default="ruri-v3-310m")
    args = ap.parse_args()
    db = ROOT / args.db
    con = sqlite3.connect(db)
    chunks = build_chunks(con)
    con.row_factory = None
    con.executescript("""
DROP TABLE IF EXISTS chunks;
CREATE TABLE chunks (chunk_id INTEGER PRIMARY KEY, kind TEXT NOT NULL, item_id INTEGER, table_id INTEGER NOT NULL,
                     text TEXT NOT NULL, sha TEXT NOT NULL);
CREATE INDEX ix_chunks_item ON chunks(item_id);
""")
    con.executemany("INSERT INTO chunks (chunk_id, kind, item_id, table_id, text, sha) VALUES (?,?,?,?,?,?)",
                    [(i, c["kind"], c["item_id"], c["table_id"], c["text"], c["sha"]) for i, c in enumerate(chunks)])
    con.execute("INSERT OR REPLACE INTO build_info VALUES ('index_embedder', ?)", (args.embedder,))
    con.commit()

    cache_f = db.parent / f"embed_cache.{args.embedder}.npz"
    cache: dict[str, np.ndarray] = {}
    if cache_f.exists():
        z = np.load(cache_f)
        cache = dict(zip(z["sha"].tolist(), z["vec"]))
    todo = [c for c in chunks if c["sha"] not in cache]
    t0 = time.time()
    if todo:
        emb = get_embedder(args.embedder)
        vecs = emb.embed_documents([c["text"] for c in todo])
        for c, v in zip(todo, vecs):
            cache[c["sha"]] = v
        np.savez(cache_f, sha=np.array(list(cache.keys())), vec=np.stack(list(cache.values())))
    mat = np.stack([cache[c["sha"]] for c in chunks]).astype(np.float32)
    np.save(db.parent / f"vectors.{args.embedder}.npy", mat)
    kinds = defaultdict(int)
    for c in chunks:
        kinds[c["kind"]] += 1
    print(f"チャンク {len(chunks)}（行 {kinds['item']}・表 {kinds['table']}）/ 新たに埋め込み {len(todo)} 件 {time.time() - t0:.0f} 秒"
          f" / 次元 {mat.shape[1]}")
    print(f"→ db/vectors.{args.embedder}.npy, DB の chunks テーブル")
    return 0


if __name__ == "__main__":
    sys.exit(main())
