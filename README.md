# 介護・障害福祉 インタフェース仕様書 RAG

国保連請求の「インタフェース仕様書」（介護・障害福祉）と、報酬の算定ルール資料（告示・留意事項通知・請求書の記載要領・Q&A・サービスコード表）を、質問から引いて答えられるようにする RAG。

- 仕様書の表は、PDF のページ画像を Claude（Haiku と Sonnet の両方）で書き起こし、両者の違いを人が確認画面で判定して確定版にしている。
- 検索は全文検索（FTS5 trigram）とベクトル検索（ruri-v3-310m）の融合。回答は Claude（Sonnet）が、引いた行・本文だけを根拠に、出典つきで書く。資料に無いことは「答えられない」と明示する。
- 各段階の経緯と評価の数字は `reports/`（`phase1_report.md`、`prod1_report.md`、`phase2_report.md` など）にある。

## 注意
- 厚生労働省・国保中央会などの公式のものではない。書き起こし・回答には誤りがありうるので、請求の実務では必ず原本（下の「出典」）を確かめること。
- 入れているのは公開されている一次資料だけ。自治体ごとの運用や、問い合わせで得た個別の指示は入れていない。
- 書き起こす頁は、PDF のテキストレイヤから「表のある頁」を判定して選んだ（`pagemeta.py`。「項番」などの見出しが手がかり）。この判定から漏れた形の表は、本文（テキストレイヤ）としてだけ入っている。2026-11-03 に罫線の表を全編で洗い出し、障害の設定例・日数の設定方法・契約情報の作成対象サービス・共通編のインタフェース一覧・都道府県編のサービス種類ごとの設定項目（異動年月日の期間ごとの 33 表）・保険者編の充当しない項目と条件は取り込んだ。介護 インターネット編（伝送の API。約 60 頁）はまだ本文だけ。

## 出典
取り込んだ資料はすべて、次の公開元が公開しているもの（調査・取得は 2026-11-01〜02）。件数は DB に入れたもの。1件ずつの一覧（資料名・原本の URL・掲載ページ・版。参考に登録しただけの新旧対照表なども含む）は **[`sources/SOURCES.md`](sources/SOURCES.md)**。

| 資料 | 公開元・掲載場所 | 件数 |
|---|---|---|
| 介護保険のインタフェース仕様書（全編。令和8年6月版。サービス事業所編・居宅介護支援事業所編は令和6年4月版、伝送のインターネット編は令和4年10月版） | [WAM NET 行政情報 > 国保連インタフェース](https://www.wam.go.jp/gyoseiShiryou/detail-list?bun=020050010)（厚生労働省老健局の事務連絡「介護保険事務処理システム変更に係る参考資料」の添付。R8.5.25 確定版 [gno=22560](https://www.wam.go.jp/gyoseiShiryou/detail?gno=22560&ct=020050010)） | 8 編（11 ファイル。保険者編は4分冊） |
| 障害福祉のインタフェース仕様書（共通編・事業所編・市町村編・都道府県編） | 厚生労働省の障害福祉の電子請求（インタフェース仕様書）の施行分ごとのページ（[令和7年10月施行分](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174643_00020.html)・[令和8年6月施行分](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174643_00025.html)） | 4 編 |
| 介護の算定ルール資料（報酬告示・留意事項通知・記載要領・Q&A・サービスコード表・総合事業） | 厚生労働省（[令和6年度介護報酬改定のページ](https://www.mhlw.go.jp/stf/newpage_38790.html)、[法令等データベース](https://www.mhlw.go.jp/hourei/) ほか）、WAM NET | 59 件 |
| 障害の算定ルール資料（改正告示・留意事項通知・Q&A・サービスコード表） | 厚生労働省（[令和8年度](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000202214_00013.html)・[令和6年度](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000202214_00009.html)の報酬改定のページ、[サービスコード表](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000174644_00022.html) ほか）、[こども家庭庁](https://www.cfa.go.jp/policies/shougaijishien/shisaku/r8hoshukaitei)（障害児） | 35 件 |

- 「最新」と判断した根拠は `sources/README.md`（仕様書）と `sources/rules_survey.md`（算定ルール資料）。取得日時と sha256 は `sources/fetch_log*.json`。
- 質問画面の回答では、出典の資料名から原本の PDF の該当ページが開く。
- `sources/SOURCES.md` は `uv run python src/list_sources.py` で manifest から作り直す。

## ライセンス
- コード（`src/`、`prompts/` など）は MIT License（`LICENSE`）。
- 原本の PDF・Excel はリポジトリに含めない（`src/fetch.py` で取得する）。`out/`・`reports/` にある書き起こしや画像は、厚生労働省などが公開している資料を写したもので、その著作権・利用条件は各原本の公開元に従う（MIT License の対象外）。

## 社内で試す（Cloud Run）
質問画面（`src/web_app.py`）を Google Cloud Run に載せ、IAP で社内の Google Workspace のドメインの人だけが開けるようにする。

1. 手元で `build_db.py` → `build_rules.py` → `build_examples.py` → `build_daysettings.py` → `build_index.py` を済ませる（`db/` の DB とベクトルをイメージに入れる）。
2. gcloud CLI を入れて `gcloud auth login`。課金を有効にしたプロジェクトを用意する。
3. `PROJECT=プロジェクトID DOMAIN=社内ドメイン bash deploy/deploy.sh all`
   - API の有効化 → `.env` の API キーを Secret Manager へ → Cloud Build でイメージを作る → Cloud Run（メモリ 4GB、最大1台、使わないときは0台）→ IAP でドメインの人に許可。
   - 1日の API 費用の上限は `MAX_USD_PER_DAY`（既定 $5）。超えるとその日は答えない。
   - ログ（Cloud Logging）には、利用者・費用・時間だけを出す。質問文も出すときは `LOG_QUESTIONS=1`。
   - 使わない間は止まるので、しばらくぶりの最初の質問は起動を待つ（数十秒）。
4. DB を作り直したら `bash deploy/deploy.sh build` → `deploy`。

## ディレクトリ
```
sources/   manifest.yaml・rules_manifest.yaml（取得対象と版情報）, SOURCES.md（出典一覧）, README.md（最新と判断した根拠）, raw/{kaigo,shogai}/（原本PDF。編集しない）, fetch_log.json
config/    pages.yaml（フェーズ1の検証対象ページ）
prompts/   transcribe_system.md, transcribe_user.md, transcribe.schema.json
deploy/   deploy.sh（Cloud Run に載せる）, requirements-web.txt。Dockerfile と .gcloudignore は直下
src/       web_app.py + web_ui.html（質問画面）, list_sources.py（出典一覧を作る）, fetch.py, transcribe.py, batch.py, pagemeta.py, postprocess.py, validate.py, report.py, adopt.py, review_app.py（確認画面）, review_core.py, apply_review.py, build_db.py（SQLite 化）, exchange_ids.py（交換情報識別番号の補完）, build_rules.py（算定ルール資料の取り込み）, transcribe_examples.py + build_examples.py（設定例を事例に）, build_daysettings.py（日数情報レコードの設定方法の表）, textlayer_tables.py + matrix_tables.py（テキストレイヤから表を組み立てる）, ocr_rules.py（画像だけのページの書き起こし）, query_db.py, build_index.py, retrieve.py, eval_retrieval.py（フェーズ2 検索）, ask.py, eval_answers.py（フェーズ2 回答）, compare_runs.py, pricing.py, llm/（LLMClient 抽象 + Anthropic 実装 + モック）
out/       {run}/{model}/{doc_id}_p{page}.json（書き起こし結果）, {run}/calls.jsonl, {run}/validation.json
reports/   phase1_report.md, pilot_report.md, prod1_report.md（各段階の報告）, review_queue.*.csv（確認キュー）, compare.html（目視比較用）, cost.md, img/
```

## 実行
```sh
uv sync
uv run python src/fetch.py                      # フェーズ0: 原本のダウンロード（sha256 照合あり。再実行するとスキップ）
uv run python src/fetch.py --manifest sources/rules_manifest.yaml   # 算定ルール資料（告示・留意事項・記載要領・Q&A・サービスコード表）→ sources/raw/rules/

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

# 本番2〜4 も同じ手順: config/prodN.yaml で plan → submit → collect、
#   postprocess.py --run prodN-png → validate.py / report.py / adopt.py / review_app.py / apply_review.py を --run prodN-png-post で
#   （本番2: 介護 居宅介護支援事業所編、本番3: 介護 都道府県編・生保単独編、本番4: 介護 保険者編・市町村合併編、障害 市町村編・都道府県編）
#   本番5: 表の判定から漏れていた表（頁を指定。障害 事業所編の契約情報の作成対象サービス・決定コードの対応、障害 共通編のインタフェース一覧）。
#     インタフェース一覧（1頁 70〜90 行の細かい表）は、画像からの書き起こしをやめて PDF のテキストレイヤと罫線から組み立てる（apply_review.py の後に毎回）
uv run python src/textlayer_tables.py --run prod5-png-post
# 画像を使わず PDF のテキストレイヤと罫線から組み立てる表（API なし。out/matrix-textlayer-reviewed/。build_db.py が既定で読む）
#   障害 都道府県編の「サービス種類ごとの設定項目」（行: サービス種類、列: 項目、○。横に数頁続く表をサービス種類でつなぐ。
#   異動年月日の期間ごとに別の表にする。障害 p54〜132 の 19 期間・障害児 p288〜314 の 14 期間）、介護 保険者編 p210〜212「データの充当を行なわない項目とその条件」
#   検索（retrieve.py）は、今の期間（〜以降）でない表を古い表として重みを下げる。質問に年月（平成30年4月 など）があれば、その年月を含む期間の表を引く
uv run python src/matrix_tables.py
# 確定版を SQLite に入れる（db/interface_spec.sqlite。表の一覧・行・列ごとの値・注記・全文検索）。既定で本番1〜5 と matrix-textlayer をすべて読む
uv run python src/build_db.py
uv run python src/query_db.py 受給者証番号 --domain shogai        # 全文検索（3文字以上）
uv run python src/query_db.py --required 0101                     # 列（様式種別番号など）で ◎ の項目
uv run python src/query_db.py --exchange J611                     # 交換情報識別番号のレコードの項目

# 算定ルール資料（告示・留意事項・記載要領・Q&A・サービスコード表）を同じ DB に入れる（API なし。build_db.py の後に毎回）
#   新旧対照表は「改正後」の欄だけ。サービスコード表は Excel から（service_codes テーブル）。判断は sources/rules_survey.md
# 画像だけのページ（介護 Q&A Vol.11・Vol.13）は、先に Claude で書き起こしておく（API、5ページ $0.08。結果は out/ocr_rules/）
uv run python src/ocr_rules.py --only kaigo_qa_r6_v11 kaigo_qa_r6_v13
uv run python src/build_rules.py

# 設定例（障害 サービス事業所編 p161〜210・p300〜305 の実績記録票設定例 63 件。障害者と障害児）: 図・表・説明を事例ごとに構造化する
#   書き起こし（API、Haiku と Sonnet の両方、56 頁 約 $1.9）→ 採用（config/examples.yaml。違いは原本と照らして決めた）
#   → DB の examples テーブル、out/examples/{doc}/examples.csv（事例1件1行）・example_cells.csv（セル1つ1行）・examples.md
uv run python src/transcribe_examples.py --doc shogai_jigyosho_r0710 --pages 161-210,300-305
uv run python src/build_examples.py                              # build_db.py の後に毎回（API なし）

# 設定方法の表（障害 サービス事業所編 p23〜30・p237〜241「日数情報レコードの設定方法」29 件。障害者と障害児）
#   サービス種類｜事務処理要領｜データ設定例 の表を、事務処理要領を共有するサービスのまとまりごとに構造化する
#   （「（N）と同様」の引き先と ※ の注記を付ける）。書き起こし（API、両モデル、13 頁 約 $0.4）→ 採用（config/daysettings.yaml）
#   → DB の day_settings テーブル、out/daysettings/{doc}/day_settings.csv（サービス1つ1行）・day_settings.md
uv run python src/transcribe_examples.py --kind daysettings --doc shogai_jigyosho_r0710 --pages 23-30,237-241
uv run python src/build_daysettings.py                           # build_db.py の後に毎回（API なし）

# フェーズ2: 検索（埋め込みはローカル GPU。torch などは依存グループ rag）
uv sync --group rag
uv run --group rag python src/build_index.py                     # 索引（build_db.py → build_rules.py → build_examples.py → build_daysettings.py の後に毎回）
uv run --group rag python src/retrieve.py "要介護度はどのコードで何桁？" --domain kaigo
uv run --group rag python src/eval_retrieval.py                  # 検索の評価 reports/retrieval_eval.md

# フェーズ2: 回答生成（Claude API。既定は Sonnet 5.5、1問 約 $0.01）
uv run --group rag python src/ask.py "要介護度はどのコードで何桁？" --domain kaigo   # 検索の前に Haiku で質問を言い換える（prompts/rewrite_system.md）
uv run --group rag python src/eval_answers.py                    # 回答の評価（両モデル、約 $0.25）

# 実際の質問での評価: eval/real_questions.txt に質問を書く → 回答 → reports/real_eval.csv の「判定」列に ○△× → 集計
uv run --group rag python src/eval_real.py run
uv run --group rag python src/eval_real.py summary

# 質問画面（ブラウザ）。http://127.0.0.1:8080/
uv run --group rag python src/web_app.py

# API を使わずにパイプラインだけ試す
uv run python src/transcribe.py --provider mock && uv run python src/validate.py --run mock-png && uv run python src/report.py --run mock-png
```

- 書き起こし結果が既にあるページはスキップする。やり直すときは `--force` を付ける。
- 既定ではページを PNG（150dpi）にしてモデルに渡す。`--input pdf` で1ページ切り出し PDF を渡す（比較用。介護の全角1桁の桁数を落とすので非推奨）。
- PDF 入力の結果は `--run anthropic-pdf` を付けて validate / report すると `reports/compare.anthropic-pdf.html` に出る。
- LLM を別のものに差し替えるときは `src/llm/base.py` の `LLMClient` を実装し、`src/llm/__init__.py` の `get_client` に登録する。
- 動作確認は Windows 11 で行った（指示書の想定は Mac）。パスはすべて pathlib で扱っているので、Mac でもそのまま動くはず。
