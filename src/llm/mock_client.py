"""API を呼ばずにパイプライン（検証・レポート）を通すためのモック。

PDF のテキストレイヤから項番らしき行を雑に拾ってスキーマ形の JSON を返す。
精度評価には使わない（--mock 実行の出力は out/mock/ に分離される）。
"""

from __future__ import annotations

import io
import json
import re
import time
import unicodedata
from typing import Any

from .base import Attachment, LLMClient, LLMResult, Usage


class MockClient(LLMClient):
    provider = "mock"

    def generate_json(self, *, model: str, attachments: list[Attachment], **_: Any) -> LLMResult:
        import pymupdf

        pdf = next(a for a in attachments if a.kind == "pdf")
        doc = pymupdf.open(stream=io.BytesIO(pdf.data), filetype="pdf")
        lines = [ln.strip() for ln in doc[0].get_text().splitlines() if ln.strip()]
        items = []
        for i, ln in enumerate(lines[:-1]):
            n = unicodedata.normalize("NFKC", ln)
            if re.fullmatch(r"\d{1,3}", n) and len(items) < 40:
                name = lines[i + 1]
                if "haiku" in model and len(items) % 7 == 3:  # 差分表示の確認用に故意にずらす
                    name = name + "（誤）"
                items.append({
                    "no": int(n), "no_raw": ln, "name_path": [name], "type": None,
                    "length": None, "length_raw": None, "content": None,
                    "required": None, "required_by": [], "note": None,
                })
        out = {
            "printed_page": None,
            "tables": [{
                "table_kind": "other", "title": None,
                "record": {"exchange_id": None, "name": None, "parent": None},
                "columns": [], "items": items,
                "continued_from_prev_page": bool(items) and items[0]["no"] != 1,
                "continues_to_next_page": False,
            }],
            "footnotes": [],
            "uncertain": ["MOCK 出力"],
        }
        text = json.dumps(out, ensure_ascii=False)
        return LLMResult(
            model=f"mock:{model}", text=text, parsed=out,
            usage=Usage(input_tokens=3000, output_tokens=len(text) // 2),
            stop_reason="end_turn", latency_s=0.0,
        )
