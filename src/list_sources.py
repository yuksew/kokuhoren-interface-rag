"""取り込んだ資料の出典一覧（sources/SOURCES.md）を、manifest から作る。

usage: uv run python src/list_sources.py
  - sources/manifest.yaml（インタフェース仕様書）と sources/rules_manifest.yaml（算定ルール資料）の全件を、
    分野・掲載ページごとに並べる。DB に入れていない資料（参考に登録しただけのもの）も「取り込み: なし」として載せる。
"""

from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUB = {"www.mhlw.go.jp": "厚生労働省", "www.wam.go.jp": "WAM NET",
       "www.cfa.go.jp": "こども家庭庁"}
DOMAIN = {"kaigo": "介護保険", "shogai": "障害福祉（障害児を含む）"}


def pub(url: str | None) -> str:
    return PUB.get(urlparse(url).hostname or "", urlparse(url).hostname or "（不明）") if url else "（不明）"


def section(title: str, entries: list[dict], ingested) -> list[str]:
    out = [f"## {title}", ""]
    for dom in DOMAIN:
        es = [e for e in entries if e["domain"] == dom]
        if not es:
            continue
        out += [f"### {DOMAIN[dom]}（{len(es)} 件）", ""]
        groups: dict[str | None, list[dict]] = defaultdict(list)
        for e in es:
            groups[e.get("source_page")].append(e)
        for page, ge in groups.items():
            head = f"掲載ページ: <{page}>（{pub(page)}）" if page else "掲載ページ: 未特定（PDF の URL だけ確認）"
            out += [f"**{head}**", ""]
            for e in ge:
                ed = " ".join(str(x) for x in (e.get("edition"), e.get("revision")) if x)
                link = f"[{e['title']}]({e['url']})" if e.get("url") else e["title"]
                tail = "" if ingested(e) else " — 取り込み: なし"
                out.append(f"- {link}" + (f"（{ed}）" if ed else "") + tail)
            out.append("")
    return out


def main() -> int:
    spec = yaml.safe_load((ROOT / "sources" / "manifest.yaml").read_text(encoding="utf-8"))
    rules = yaml.safe_load((ROOT / "sources" / "rules_manifest.yaml").read_text(encoding="utf-8"))
    hosts = sorted({pub(e.get("url")) for e in spec + rules if e.get("url")})
    lines = [
        "# 出典一覧",
        "",
        "`src/list_sources.py` が `sources/manifest.yaml`・`sources/rules_manifest.yaml` から作る（手で直さない）。",
        "最新と判断した根拠は `sources/README.md`・`sources/rules_survey.md`。取得日時と sha256 は `fetch_log*.json`。",
        "",
        "公開元: " + "、".join(hosts) + "（WAM NET は独立行政法人福祉医療機構のサイトで、厚生労働省の事務連絡と添付資料を載せている）",
        "",
        "どれも公開されている一次資料で、原本の PDF・Excel はリポジトリに含めない（`src/fetch.py` で取得する）。"
        "書き起こしの著作権・利用条件は各原本の公開元に従う。",
        "",
    ]
    # 取り込んだかどうかは DB で見る（manifest には参考に登録しただけの資料もある）
    con = sqlite3.connect(ROOT / "db" / "interface_spec.sqlite")
    used = {r[0] for r in con.execute("SELECT doc_id FROM documents UNION SELECT doc_id FROM rule_docs")}
    lines += section(f"インタフェース仕様書・事務連絡（{len(spec)} 件）", spec, lambda e: e["id"] in used)
    lines += section(f"算定ルール資料（{len(rules)} 件）", rules, lambda e: e["id"] in used)
    (ROOT / "sources" / "SOURCES.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"sources/SOURCES.md: 仕様書 {len(spec)} 件、算定ルール資料 {len(rules)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
