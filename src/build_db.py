"""確定版（人の確認を反映した書き起こし）を SQLite に入れる。RAG の検索の土台。

usage: uv run python src/build_db.py [--run prod1-png-post] [--src reviewed|adopted] [--out db/interface_spec.sqlite]
  前提: apply_review.py を実行済み（out/{run}-reviewed/ がある）
  DB は毎回作り直す（入力から再生成できるので git には入れない）。

テーブル
  documents      文書（版）。sources/manifest.yaml の内容
  pages          ページ（印刷ページ番号・ページ下の注記）
  spec_tables    論理的な表（ページをまたぐ表は結合済み）
  items          表の行（項番ごと）。name は最下段の項目名、name_full は階層つき
  item_values    行の列ごとの値（必須対応表の ◎○△、インタフェース一覧の識別・周期など）
  item_notes     行に付いた「※n」注記の本文
  items_fts      全文検索（FTS5 trigram: 3文字以上の部分一致）
  v_items        よく使う結合のビュー（文書・版・ページつき）
  build_info     作成日時・入力
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_core import col_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE documents (
  doc_id TEXT PRIMARY KEY, domain TEXT NOT NULL, title TEXT, volume TEXT, edition TEXT, revision TEXT,
  published_at TEXT, url TEXT, source_page TEXT, sha256 TEXT, note TEXT
);
CREATE TABLE pages (
  doc_id TEXT NOT NULL REFERENCES documents(doc_id), page INTEGER NOT NULL, printed_page TEXT,
  footnotes TEXT,             -- JSON [{mark, text}]
  uncertain TEXT,             -- JSON [..] 書き起こし時の不確かな点
  PRIMARY KEY (doc_id, page)
);
CREATE TABLE spec_tables (
  table_id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES documents(doc_id), seq INTEGER NOT NULL,
  title TEXT, table_kind TEXT, record_exchange_id TEXT, record_name TEXT, record_parent TEXT,
  page_from INTEGER, page_to INTEGER, pages TEXT,        -- pages は JSON 配列
  columns TEXT, column_map TEXT,                          -- JSON
  source_model TEXT, starts_mid_table INTEGER, no_min INTEGER, no_max INTEGER, no_gaps TEXT
);
CREATE TABLE items (
  item_id INTEGER PRIMARY KEY, table_id INTEGER NOT NULL REFERENCES spec_tables(table_id), seq INTEGER NOT NULL,
  doc_id TEXT NOT NULL, page INTEGER,
  no INTEGER, no_raw TEXT, name TEXT, name_full TEXT, group_path TEXT,
  type TEXT, length INTEGER, length_raw TEXT, content TEXT, required TEXT, note TEXT,
  fixes TEXT,                 -- JSON: 自動修正（textlayer）・人の修正（human）の記録
  human_fixed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE item_values (
  item_id INTEGER NOT NULL REFERENCES items(item_id), kind TEXT NOT NULL,  -- required_by | cell
  column_name TEXT NOT NULL, column_key TEXT, value TEXT
);
CREATE TABLE item_notes (
  item_id INTEGER NOT NULL REFERENCES items(item_id), mark TEXT, text TEXT, source TEXT
);
CREATE TABLE build_info (key TEXT PRIMARY KEY, value TEXT);
CREATE INDEX ix_items_table ON items(table_id, seq);
CREATE INDEX ix_items_doc_page ON items(doc_id, page);
CREATE INDEX ix_items_name ON items(name);
CREATE INDEX ix_values_item ON item_values(item_id);
CREATE INDEX ix_values_col ON item_values(column_key, value);
CREATE INDEX ix_tables_exchange ON spec_tables(record_exchange_id);
CREATE VIRTUAL TABLE items_fts USING fts5(
  name_full, content, note, values_text, table_title, tokenize='trigram'
);
CREATE VIEW v_items AS
SELECT i.item_id, d.domain, d.volume, d.edition, i.doc_id, i.page, p.printed_page,
       t.table_id, t.title AS table_title, t.table_kind, t.record_exchange_id, t.record_name,
       i.no, i.no_raw, i.name, i.name_full, i.type, i.length, i.length_raw, i.content, i.required, i.note, i.human_fixed
FROM items i JOIN spec_tables t USING (table_id) JOIN documents d ON d.doc_id = i.doc_id
LEFT JOIN pages p ON p.doc_id = i.doc_id AND p.page = i.page;
"""


def js(v) -> str | None:
    return None if v is None else json.dumps(v, ensure_ascii=False)


def blank(v) -> str | None:
    return None if v in (None, "") else str(v)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="prod1-png-post")
    ap.add_argument("--src", default="reviewed", choices=["reviewed", "adopted"])
    ap.add_argument("--out", default="db/interface_spec.sqlite")
    args = ap.parse_args()
    src = ROOT / "out" / f"{args.run}-{args.src}"
    logical = json.loads((src / "logical_tables.json").read_text(encoding="utf-8"))
    manifest = {e["id"]: e for e in yaml.safe_load((ROOT / "sources" / "manifest.yaml").read_text(encoding="utf-8"))}

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)

    docs = sorted({lt["doc_id"] for lt in logical})
    for d in docs:
        e = manifest[d]
        con.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (d, e["domain"], e.get("title"), e.get("volume"), e.get("edition"), e.get("revision"),
                     str(e.get("published_at") or ""), e.get("url"), e.get("source_page"), e.get("sha256"), e.get("note")))
    for f in sorted(src.glob("*_p*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        con.execute("INSERT INTO pages VALUES (?,?,?,?,?)", (p["doc_id"], p["page"], blank(p.get("printed_page")),
                                                            js(p.get("footnotes") or []), js(p.get("uncertain") or [])))

    stats = Counter()
    seq_by_doc = Counter()
    for lt in logical:
        seq_by_doc[lt["doc_id"]] += 1
        rec = lt.get("record") or {}
        nr = lt.get("no_range") or [None, None]
        cur = con.execute(
            "INSERT INTO spec_tables (doc_id, seq, title, table_kind, record_exchange_id, record_name, record_parent, page_from, page_to,"
            " pages, columns, column_map, source_model, starts_mid_table, no_min, no_max, no_gaps) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (lt["doc_id"], seq_by_doc[lt["doc_id"]], blank(lt.get("title")), lt.get("table_kind"), blank(rec.get("exchange_id")),
             blank(rec.get("name")), blank(rec.get("parent")), min(lt["pages"]), max(lt["pages"]), js(lt["pages"]),
             js(lt.get("columns")), js(lt.get("column_map")), lt.get("source_model"), int(bool(lt.get("starts_mid_table"))),
             nr[0], nr[1], js(lt.get("no_gaps"))))
        tid = cur.lastrowid
        stats["tables"] += 1
        for i, it in enumerate(lt["items"]):
            path = [x for x in it.get("name_path") or [] if x]
            fixes = it.get("_fixes") or []
            human = any(fx.get("by") == "human" for fx in fixes)
            cur = con.execute(
                "INSERT INTO items (table_id, seq, doc_id, page, no, no_raw, name, name_full, group_path, type, length, length_raw,"
                " content, required, note, fixes, human_fixed) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (tid, i + 1, lt["doc_id"], it.get("page"), it.get("no"), blank(it.get("no_raw")), path[-1] if path else None,
                 " > ".join(path) or None, " > ".join(path[:-1]) or None, blank(it.get("type")), it.get("length"),
                 blank(it.get("length_raw")), blank(it.get("content")), blank(it.get("required")), blank(it.get("note")),
                 js(fixes) if fixes else None, int(human)))
            iid = cur.lastrowid
            stats["items"] += 1
            stats["human_fixed"] += human
            vals = []
            for kind, key in (("required_by", "required_by"), ("cell", "cells")):
                for e in it.get(key) or []:
                    if e.get("value") in (None, ""):
                        continue
                    con.execute("INSERT INTO item_values VALUES (?,?,?,?,?)",
                                (iid, kind, e.get("column") or "", col_key(e.get("column")), str(e["value"])))
                    vals.append(f"{e.get('column')}: {e['value']}")
                    stats["values"] += 1
            for n in it.get("note_refs") or []:
                con.execute("INSERT INTO item_notes VALUES (?,?,?,?)", (iid, n.get("mark"), n.get("text"), n.get("source")))
                stats["notes"] += 1
            con.execute("INSERT INTO items_fts (rowid, name_full, content, note, values_text, table_title) VALUES (?,?,?,?,?,?)",
                        (iid, " > ".join(path), it.get("content") or "", it.get("note") or "", "\n".join(vals), lt.get("title") or ""))

    dec = ROOT / "reports" / f"review_decisions.{args.run}.json"
    info = {"built_at": dt.datetime.now().isoformat(timespec="seconds"), "run": args.run, "source": str(src.relative_to(ROOT)),
            "review_decisions_sha256": hashlib.sha256(dec.read_bytes()).hexdigest() if dec.exists() else "",
            "docs": ",".join(docs)}
    con.executemany("INSERT INTO build_info VALUES (?,?)", info.items())
    con.commit()
    con.execute("VACUUM")
    con.close()
    out.unlink(missing_ok=True)
    tmp.replace(out)
    print(f"文書 {len(docs)} / 表 {stats['tables']} / 行 {stats['items']}（人が修正 {stats['human_fixed']}）"
          f" / 列の値 {stats['values']} / 注記 {stats['notes']}")
    print(f"→ {out.relative_to(ROOT)}（{out.stat().st_size / 1e6:.1f} MB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
