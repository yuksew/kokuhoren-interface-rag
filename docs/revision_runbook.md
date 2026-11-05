# 改定の取り込み手順書

報酬改定・制度改正のたびに出る新しいインタフェース仕様書と算定ルール資料を、RAG に取り込む手順。
最初に書いたのは 2026-11-05（令和9年度改定の準備中）。

## 方針

- **入れるのは一次資料だけ**（厚生労働省・WAM NET・こども家庭庁）。審議会の資料は改定の時期を知るために見るが、取り込まない。民間の整理版は入れない。
- **今の版と次の版の両方を入れ、施行日で切り替える。**
  - 今の版は、施行日より前のサービス提供分の請求にも使い続けられる。
  - 次の版は、施行日までは「施行前の次の版」として重みを下げる。「令和9年」「改定後」「次期」などと聞かれたときは下げない。
  - 回答では、次の版の抜粋に【施行前の次の版（案）】【施行前の次の版】と、旧版の抜粋に【旧版】と付く。
- **切り替えは manifest の値で決まる。** 施行日の当日に作業は要らない。
  - `effective`（施行日）・`status`（`final` | `draft`）から、`build_db.py` が版の期間 `valid_from`〜`valid_to` を計算する（同じ編の次の確定版の施行日まで）。
  - 検索（`retrieve.py`）は、基準日（既定は今日）と質問の年月でどの版を今の版とするかを決める。
- **案（`status: draft`）は、いつまでも「次の版」のまま。** 確定版を取り込んだら、案は外す（「6. 施行日の確定と切り替え」）。

## 令和9年度改定の見込み（2026-11-05 時点）

| | 介護 | 障害福祉 |
|---|---|---|
| インタフェース仕様書 | 「参考資料（その１）」（R8.10.6）と「国保連合会とのインタフェースの変更点（2027年5月以降出力分）」が出ている。この 2 件は案として取り込み済み（`kaigo_notice_20261006`・`kaigo_if_changes_20261002`、`status: draft`）。変更点資料には「事業所のシステム改修」も含むとあり、サービス事業所編も変わる見込み | まだ何も出ていない（一覧ページの最新は「31 令和8年6月施行分」） |
| これまでの出方 | その１（前年の秋）→ その２〜その６ → 確定版（3月末）→ 一部修正（5月ごろ）。平成30年度・令和3年度・令和6年度とも同じ | 施行分ごとのページに「事務連絡（案）」→「【確定版】」。全編が出し直されるとは限らず、変わった編だけが載る |
| 改定の審議 | 介護給付費分科会。12月に基本的な考え方をまとめ、令和9年1月ごろに諮問・答申の予定 | 報酬改定検討チーム。12月に基本的な考え方をまとめ、令和9年2月に改定案の予定 |
| 施行日 | **未確定。** 第272回分科会（R8.10.28）で 6月1日施行の考えが示されたと報じられているが、一次資料ではまだ確かめていない。予算編成の後に決まる | 未確定 |

施行日が決まるまで、次の版の `effective` は `null` のままにする（日付を推測で入れない）。

## 1. 新着の確認

```sh
uv run python src/watch.py            # 新着があれば reports/watch/{日付}.md に書き、終了コード 10
uv run python src/watch.py --dry-run  # 状態（sources/watch_state.json）を書き換えずに見るだけ
```

- 見るページは `sources/watch.yaml`。令和9年度の改定ページ（介護報酬・障害の報酬改定）ができたら、そのページも足す（今の令和8年度のページと同じ書き方）。
- 頻度の目安: ふだんは月 1 回。改定の年の 12 月〜5 月は週 1 回（その２以降・確定版・Q&A・正誤が続けて出る）。
- 「リンクが 1 つも無い」と出たら、ページの作りが変わっている。`include` を見直す。

## 2. 判定（新着を取り込むか）

| 新着 | すること |
|---|---|
| 介護「参考資料（その◯）」（WAM NET） | 中身を見る。仕様書の全文（全量版）か、変更点資料・新旧対照表だけか。変更点・新旧対照表は案として本文で取り込む（3〜4）。仕様書の全文は、原則として確定版を待つ（早く要るなら案として取り込む） |
| 介護「参考資料（確定版）」 | 取り込む。編ごとに「（変更なし）」の表示を見る。リンク先が前の版と同じファイル（sha256 が同じ）なら、その編は新しい版を作らない |
| 障害「◯年◯月施行分」のページ | 事務連絡の「（案）」「【確定版】」を見る。施行分のページに載っている編だけが変わる |
| 告示・改正告示 | 取り込む（算定ルール）。告示の全文（法令等データベース）があれば全文、無ければ改正告示を日付つきで積む |
| 留意事項通知の一部改正（新旧対照表） | 取り込む。改正後の欄だけが入る（`build_rules.py`）。1 つの PDF に別紙がいくつも入っていれば `pages` で頁を分ける。改正後が右の欄なら `new_side: right` |
| Q&A・正誤 | 取り込む。正誤は `category: errata` |
| サービスコード表 | Excel 版を取り込む（`ingest: table`）。PDF は参考 |
| 審議会の資料・報道発表 | 取り込まない。改定案・答申・施行日が出たかを見る |

## 3. 登録（manifest）

- **インタフェース仕様書**（`sources/manifest.yaml`）
  - id は `{分野}_{編}_r{年}{月}`（例: `kaigo_jigyosho_r0906`）。前の版の id は変えない。
  - `edition`・`revision`・`kind`（`spec` | `revision_history` | `notice`）・`published_at`・`url`・`source_page` を書く。
  - `status`: 案は `draft`、確定版は `final`（書かなければ `final`）。
  - `effective`: 施行日が決まるまで `null`。書かなければ版の名前（「令和9年6月版」など）から読む。
  - `sha256: null` で登録すると、`fetch.py` が取得したときに書き込む。
- **算定ルール資料**（`sources/rules_manifest.yaml`）: `category`・`edition`・`effective`・`format`・`ingest`。必要なら `pages`・`new_side`。
- 取得と出典一覧:

```sh
uv run python src/fetch.py --only <id>...
uv run python src/fetch.py --manifest sources/rules_manifest.yaml --only <id>...
uv run python src/list_sources.py   # sources/SOURCES.md を作り直す
```

## 4. 取り込み

### インタフェース仕様書（表のある編）

これまでの本番1〜6 と同じ手順（README の「実行」）。変わった編だけを書き起こす。

1. `uv run python src/pagemeta.py` で表のある頁を判定する。表の判定から漏れる形の表（縦書きの見出しの表、横に数頁続く表など）がないか、罫線の表を洗い出して確かめる（本番5・`matrix_tables.py` の経緯）。
2. `config/prodN.yaml` に頁を書き、`batch.py plan` → `submit` → `status` → `collect`。費用の目安は Batch で 1 頁 約 $0.025（Haiku + Sonnet）。
3. `postprocess.py` → `validate.py` → `report.py` → `adopt.py`。
4. 確認キューを判定する。PDF に文字があれば、テキストレイヤの同じ番号の行と照らして機械的に決められる（本番6 の方法）。残りは原本の画像と照らす（`review_app.py`）。
5. `apply_review.py`。細かい一覧表は `textlayer_tables.py` で組み立て直す。
6. `build_db.py` の既定の `--run` に `prodN-png-post` を足す。

### 本文だけの資料（事務連絡・変更点資料・修正履歴）

`build_db.py` の `PROSE_ONLY` に id を足す。`build_index.py` が PDF のテキストレイヤから本文のチャンクを作る。

修正履歴・新旧対照表（`kind: revision_history`）は、今は登録だけで取り込んでいない。「何が変わったか」を聞かれることが多ければ、本文として取り込む。

### 作り直し（毎回この順）

```sh
uv run python src/build_db.py
uv run python src/build_rules.py
uv run python src/build_examples.py
uv run python src/build_daysettings.py
uv run --group rag python src/build_index.py
```

## 5. 確認・評価

```sh
uv run --group rag python src/eval_retrieval.py                         # 基準日 2026-11-05（固定）
uv run --group rag python src/eval_retrieval.py --as-of 2027-06-01 --out reports/retrieval_eval.after.md   # 施行日の後として
uv run --group rag python src/eval_answers.py --models claude-sonnet-5-5 --out reports/answer_eval.sonnet_NNq.md   # 約 $1
```

- 前からある質問で順位が下がったものがないかを見る（`git diff reports/retrieval_eval.md`）。
- 新しい版の質問を `eval/questions.yaml` に足す。施行前は `kind: next`（「令和9年度の改定で〜」）。今の版の同じ項目の質問も 1 問足し、次の版が今の版として答えられないことを確かめる。
- 評価の基準日は `eval_retrieval.py`・`eval_answers.py` の `AS_OF`。施行日を過ぎたら、施行後の日付に更新し、施行前の質問（`kind: next`）を見直す。

## 6. 施行日の確定と切り替え

1. 施行日が告示・事務連絡で決まったら、次の版の `effective` に入れる。
2. 確定版を取り込んだら、同じ内容の案を外す。
   - manifest の案の項目は `status: superseded` にし、`build_db.py` の `PROSE_ONLY` から外す（manifest には記録として残す）。
   - 案の変更点資料と確定版の変更点資料は、別の資料として登録する。
3. 施行日の当日は作業不要。検索は基準日（今日）で今の版を選び直す。
4. 施行日の後に、`--as-of` を施行後の日付にして評価を回す。README・`sources/README.md`・`sources/SOURCES.md` の「最新」の記述を更新する。

## 7. 記録

- `sources/README.md`: 最新と判断した根拠（どのページの、どの記載か）。
- `sources/rules_survey.md`: 算定ルール資料の判断。
- README の「出典」の件数。
- コミットは段階ごとに（登録・取得 → 取り込み → 評価）。
