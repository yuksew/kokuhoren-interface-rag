"""SQLite の仕様書 DB を引く（動作確認用）。

usage:
  uv run python src/query_db.py 受給者証番号                 # 項目名・内容・備考などの全文検索（3文字以上）
  uv run python src/query_db.py 受給者証番号 --domain shogai
  uv run python src/query_db.py --required 0101             # 列（様式種別番号など）で ◎ の項目
  uv run python src/query_db.py --exchange J611             # 交換情報識別番号のレコードの項目
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = {"kaigo": "介護", "shogai": "障害"}


def cite(r) -> str:
    pp = f"（印刷 {r['printed_page']}）" if r["printed_page"] else ""
    return f"{DOMAIN.get(r['domain'], r['domain'])} {r['volume']} {r['edition']} PDF p{r['page']}{pp}"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--domain", choices=["kaigo", "shogai"])
    ap.add_argument("--required", metavar="列キー", help="例: 0101（様式種別番号）")
    ap.add_argument("--exchange", metavar="識別番号", help="例: 7111, J121")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--db", default="db/interface_spec.sqlite")
    args = ap.parse_args()
    con = sqlite3.connect(ROOT / args.db)
    con.row_factory = sqlite3.Row
    where, params = [], []
    if args.domain:
        where.append("v.domain = ?")
        params.append(args.domain)
    if args.exchange:
        where.append("v.table_id IN (SELECT table_id FROM table_exchange_ids WHERE exchange_id = ?)")
        params.append(args.exchange)
    if args.required:
        sql = ("SELECT v.*, iv.value AS mark FROM item_values iv JOIN v_items v USING (item_id) "
               "WHERE iv.column_key = ? AND iv.value LIKE '◎%'" + "".join(f" AND {w}" for w in where) + " ORDER BY v.item_id LIMIT ?")
        rows = con.execute(sql, [args.required, *params, args.limit]).fetchall()
    elif args.text:
        if len(args.text) < 3:
            print("全文検索は3文字以上で指定してください（trigram）")
            return 1
        sql = ("SELECT v.* FROM items_fts f JOIN v_items v ON v.item_id = f.rowid WHERE items_fts MATCH ?"
               + "".join(f" AND {w}" for w in where) + " ORDER BY rank LIMIT ?")
        rows = con.execute(sql, ['"' + args.text.replace('"', '""') + '"', *params, args.limit]).fetchall()
    elif args.exchange:
        sql = "SELECT v.* FROM v_items v WHERE " + " AND ".join(where) + " ORDER BY v.item_id LIMIT ?"
        rows = con.execute(sql, [*params, args.limit]).fetchall()
    else:
        ap.print_help()
        return 1
    for r in rows:
        spec = " ".join(x for x in [r["type"], f"{r['length_raw'] or r['length']}桁" if (r["length_raw"] or r["length"]) else None,
                                    f"必須{r['required']}" if r["required"] else None] if x)
        print(f"■ {r['name_full']}  [{spec}]  項番 {r['no_raw'] or r['no'] or '-'}")
        ex = f"  識別番号 {r['record_exchange_id']}" if r["record_exchange_id"] else ""
        print(f"   表: {r['table_title'] or '(無題)'}{ex}  出典: {cite(r)}")
        if r["content"]:
            print("   内容: " + r["content"].replace("\n", " / ")[:160])
    print(f"({len(rows)} 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
