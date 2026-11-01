# 介護・障害福祉 インタフェース仕様書 RAG（フェーズ0〜1）

国保連請求の「インタフェース仕様書」を RAG で引けるようにするための下準備。
今はフェーズ0（最新版の特定と取得）とフェーズ1（表の書き起こし精度の検証）だけを実装している。

## ディレクトリ
```
sources/   manifest.yaml（取得対象と版情報）, README.md（最新と判断した根拠）, raw/{kaigo,shogai}/（原本PDF。編集しない）, fetch_log.json
config/    pages.yaml（フェーズ1の検証対象ページ）
prompts/   transcribe_system.md, transcribe_user.md, transcribe.schema.json
src/       fetch.py, transcribe.py, batch.py, pagemeta.py, postprocess.py, validate.py, report.py, adopt.py, review_app.py（確認画面）, review_core.py, apply_review.py, build_db.py（SQLite 化）, exchange_ids.py（交換情報識別番号の補完）, query_db.py, build_index.py, retrieve.py, eval_retrieval.py（フェーズ2 検索）, ask.py, eval_answers.py（フェーズ2 回答）, compare_runs.py, pricing.py, llm/（LLMClient 抽象 + Anthropic 実装 + モック）
out/       {run}/{model}/{doc_id}_p{page}.json（書き起こし結果）, {run}/calls.jsonl, {run}/validation.json
reports/   phase1_report.md, pilot_report.md, prod1_report.md（各段階の報告）, review_queue.*.csv（確認キュー）, compare.html（目視比較用）, cost.md, img/
```

## 実行
```sh
uv sync
uv run python src/fetch.py                      # フェーズ0: 原本のダウンロード（sha256 照合あり。再実行するとスキップ）

# フェーズ1（ANTHROPIC_API_KEY が必要。環境変数か、プロジェクト直下の .env に ANTHROPIC_API_KEY=... と書く）
uv run python src/transcribe.py                 # Haiku 5.5 と Sonnet 5.5 で config/pages.yaml の全ページを書き起こす
uv run python src/validate.py                   # 自動チェック → out/anthropic-png/validation.json
uv run python src/report.py                     # reports/compare.html と reports/cost.md を作る

# 後処理（LLM を使わない。継続フラグの判定し直し・必須列の補完・注記のひも付け・分断された表の結合）
uv run python src/pagemeta.py                   # テキストレイヤからページ情報（表の有無・継続）→ out/pagemeta/
uv run python src/postprocess.py                # → out/anthropic-png-post/（logical_tables.json を含む）
uv run python src/validate.py --run anthropic-png-post && uv run python src/report.py --run anthropic-png-post

# 多数ページの本番処理（Batch API、料金50%）: 投入 → 待つ → 回収 → 後処理 → 検証 → 採用版と確認キュー
uv run python src/batch.py plan    --config config/prod1.yaml   # 対象ページ数と費用の見積もり
uv run python src/batch.py submit  --config config/prod1.yaml
uv run python src/batch.py status  --config config/prod1.yaml
uv run python src/batch.py collect --config config/prod1.yaml
uv run python src/postprocess.py --run prod1-png && uv run python src/validate.py --run prod1-png-post
uv run python src/report.py --run prod1-png-post               # reports/compare.prod1-png-post.html
uv run python src/adopt.py --run prod1-png-post                # 採用版 out/prod1-png-post-adopted/ と reports/review_queue.prod1-png-post.csv

# 確認キューを人が判定する（ブラウザが開く。判定は reports/review_decisions.prod1-png-post.json に即保存）
uv run python src/review_app.py
uv run python src/apply_review.py                              # 判定を反映した確定版 out/prod1-png-post-reviewed/ と reports/review_status.*.csv

# 確定版を SQLite に入れる（db/interface_spec.sqlite。表の一覧・行・列ごとの値・注記・全文検索）
uv run python src/build_db.py
uv run python src/query_db.py 受給者証番号 --domain shogai        # 全文検索（3文字以上）
uv run python src/query_db.py --required 0101                     # 列（様式種別番号など）で ◎ の項目
uv run python src/query_db.py --exchange J611                     # 交換情報識別番号のレコードの項目

# フェーズ2: 検索（埋め込みはローカル GPU。torch などは依存グループ rag）
uv sync --group rag
uv run --group rag python src/build_index.py                     # 索引（build_db.py の後に毎回）
uv run --group rag python src/retrieve.py "要介護度はどのコードで何桁？" --domain kaigo
uv run --group rag python src/eval_retrieval.py                  # 検索の評価 reports/retrieval_eval.md

# フェーズ2: 回答生成（Claude API。既定は Sonnet 5.5、1問 約 $0.01）
uv run --group rag python src/ask.py "要介護度はどのコードで何桁？" --domain kaigo
uv run --group rag python src/eval_answers.py                    # 回答の評価（両モデル、約 $0.25）

# 実際の質問での評価: eval/real_questions.txt に質問を書く → 回答 → reports/real_eval.csv の「判定」列に ○△× → 集計
uv run --group rag python src/eval_real.py run
uv run --group rag python src/eval_real.py summary

# API を使わずにパイプラインだけ試す
uv run python src/transcribe.py --provider mock && uv run python src/validate.py --run mock-png && uv run python src/report.py --run mock-png
```

- 書き起こし結果が既にあるページはスキップする。やり直すときは `--force` を付ける。
- 既定ではページを PNG（150dpi）にしてモデルに渡す。`--input pdf` で1ページ切り出し PDF を渡す（比較用。介護の全角1桁の桁数を落とすので非推奨）。
- PDF 入力の結果は `--run anthropic-pdf` を付けて validate / report すると `reports/compare.anthropic-pdf.html` に出る。
- LLM を別のものに差し替えるときは `src/llm/base.py` の `LLMClient` を実装し、`src/llm/__init__.py` の `get_client` に登録する。
- 動作確認は Windows 11 で行った（指示書の想定は Mac）。パスはすべて pathlib で扱っているので、Mac でもそのまま動くはず。
