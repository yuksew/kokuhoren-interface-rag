"""sources/manifest.yaml に載っているファイルを sources/raw/{domain}/ にダウンロードする。

- 既に同名ファイルがあり、manifest の sha256 と一致すればスキップ（再実行で同じ結果）。
- manifest の sha256 が null のときはダウンロード後に記入する。
- manifest の sha256 と異なる内容が落ちてきた場合は上書きせず、エラーとして報告する
  （公開元でファイルが差し替えられた可能性があるため。--accept-changed で受け入れ）。
- 元ファイルは一切加工しない。

usage: uv run python src/fetch.py [--manifest sources/rules_manifest.yaml] [--only ID ...] [--accept-changed]
  --manifest を省くとインタフェース仕様書（sources/manifest.yaml → sources/raw/）。
  算定ルール資料は sources/rules_manifest.yaml → sources/raw/rules/（ログは sources/fetch_log.rules.json）。
- format: html_pages のエントリ（厚労省 法令等データベース）は、pageNo=1 から「該当ページ数： N」まで取得し、
  区切り行 <!-- page N --> でつないだ1つの .html にする。
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "sources" / "manifest.yaml"
RAW = ROOT / "sources" / "raw"
LOG = ROOT / "sources" / "fetch_log.json"
UA = "Mozilla/5.0 (kokuhoren-interface-rag fetcher; research use)"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path(entry: dict, raw: Path = RAW) -> Path:
    if entry.get("format") == "html_pages":
        ext = ".html"
    else:
        ext = Path(entry["url"].split("?")[0]).suffix or ".bin"
    return raw / entry["domain"] / f"{entry['id']}{ext}"


def download_html_pages(url: str, dest: Path) -> int:
    """法令等データベース（t_doc?...&pageNo=1）の全ページを1ファイルにつなぐ。ページ数を返す。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    parts, n, page = [], 1, 1
    while page <= n:
        u = re.sub(r"pageNo=\d+", f"pageNo={page}", url)
        r = requests.get(u, headers={"User-Agent": UA}, timeout=(15, 120))
        r.raise_for_status()
        r.encoding = "utf-8"
        if page == 1:
            m = re.search(r"該当ページ数：\s*(?:<span>)?\s*(\d+)", r.text)
            if m:
                n = int(m.group(1))
            elif 'class="pageNum"' not in r.text and "○" in r.text:
                n = 1  # 1ページだけの告示にはページ数の表示が無い
            else:
                raise RuntimeError("「該当ページ数」が見つからない（ページの形式が変わった？）")
        parts.append(f"<!-- page {page} -->\n{r.text}")
        page += 1
        time.sleep(1)
    dest.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    return n


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(3):
        try:
            with requests.get(url, headers={"User-Agent": UA}, stream=True, timeout=(15, 300)) as r:
                r.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
            head = tmp.read_bytes()[:5]
            if dest.suffix.lower() == ".pdf" and head != b"%PDF-":
                raise RuntimeError(f"PDFではない応答: {head!r}")
            tmp.replace(dest)
            return
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                tmp.unlink(missing_ok=True)
                raise
            print(f"  retry ({e})", file=sys.stderr)
            time.sleep(3 * (attempt + 1))


def pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001
        return None


def write_sha_back(text: str, entry_id: str, sha: str) -> str:
    """コメントを壊さないよう、該当 id のブロック内の sha256 行だけを書き換える。"""
    pat = re.compile(
        rf"(^- id: {re.escape(entry_id)}\n(?:(?!^- id: ).*\n)*?\s+sha256: )(\S+)",
        re.M,
    )
    new, n = pat.subn(lambda m: m.group(1) + sha, text, count=1)
    if n != 1:
        raise RuntimeError(f"manifest の sha256 行が見つからない: {entry_id}")
    return new


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="sources/manifest.yaml")
    ap.add_argument("--only", nargs="*", help="指定した id だけ処理")
    ap.add_argument("--accept-changed", action="store_true", help="sha256 不一致でも新しい内容を受け入れる")
    args = ap.parse_args()

    manifest = ROOT / args.manifest
    rules = manifest.name != "manifest.yaml"
    raw = RAW / "rules" if rules else RAW
    log_f = LOG.with_name("fetch_log.rules.json") if rules else LOG
    text = manifest.read_text(encoding="utf-8")
    entries = yaml.safe_load(text)
    ids = [e["id"] for e in entries]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        print(f"id 重複: {dup}", file=sys.stderr)
        return 2

    log = json.loads(log_f.read_text(encoding="utf-8")) if log_f.exists() else {}
    errors = []
    for e in entries:
        if args.only and e["id"] not in args.only:
            continue
        if e.get("status") == "future" or not e.get("url"):
            print(f"future {e['id']}（登録だけ）")
            continue
        dest = local_path(e, raw)
        expected = e.get("sha256")
        if dest.exists() and expected and sha256_of(dest) == expected:
            print(f"skip  {e['id']}")
            continue
        tmp_dest = dest.with_name(dest.name + ".new")
        # 同じ URL の資料（1 つの PDF の別紙ごとに分けて登録したもの）を取得済みなら、それを写す
        same = next((ROOT / log[x["id"]]["file"] for x in entries if x is not e and x.get("url") == e["url"] and x["id"] in log
                     and (ROOT / log[x["id"]]["file"]).exists() and expected in (None, log[x["id"]]["sha256"])), None)
        try:
            if same is not None:
                print(f"copy  {e['id']}  <- {same.relative_to(ROOT).as_posix()}")
                shutil.copyfile(same, tmp_dest)
            else:
                print(f"get   {e['id']}  <- {e['url']}")
                if e.get("format") == "html_pages":
                    download_html_pages(e["url"], tmp_dest)
                else:
                    download(e["url"], tmp_dest)
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{e['id']}: ダウンロード失敗 {ex}")
            continue
        sha = sha256_of(tmp_dest)
        if expected and sha != expected and not args.accept_changed:
            errors.append(f"{e['id']}: sha256 不一致（公開元で差し替え？） expected={expected} got={sha}。{tmp_dest} に保存")
            continue
        tmp_dest.replace(dest)
        if expected != sha:
            text = write_sha_back(text, e["id"], sha)
        log[e["id"]] = {
            "file": dest.relative_to(ROOT).as_posix(),
            "bytes": dest.stat().st_size,
            "pages": pdf_pages(dest) if dest.suffix.lower() == ".pdf" else
                     (dest.read_text(encoding="utf-8").count("<!-- page ") if dest.suffix == ".html" else None),
            "sha256": sha,
            "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        }

    manifest.write_text(text, encoding="utf-8", newline="\n")
    log_f.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if errors:
        print("\nERRORS:", *errors, sep="\n  ", file=sys.stderr)
        return 1
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
