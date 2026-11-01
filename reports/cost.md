# 書き起こしコスト（run: anthropic-png）

単価（USD / 100万トークン）: claude-haiku-5-5 入力$0.1 出力$0.5, claude-sonnet-5-5 入力$2.0 出力$10.0。Batch API は 50% 引き。

## 呼び出しごと

| モデル | ページ | 種類 | 入力tok | 出力tok | 秒 | 通常$ | Batch$ | stop |
|---|---|---|--:|--:|--:|--:|--:|---|
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p80 | merged・split | 7,813 | 5,343 | 19.34 | 0.0035 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p81 | merged・split | 7,813 | 5,261 | 18.2 | 0.0034 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p84 | simple | 7,813 | 3,935 | 15.12 | 0.0027 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_jigyosho_r0604 p110 | matrix | 7,813 | 7,892 | 25.08 | 0.0047 | 0.0024 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p12 | simple | 7,809 | 4,067 | 16.94 | 0.0028 | 0.0014 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p35 | merged・split | 7,809 | 5,077 | 18.61 | 0.0033 | 0.0017 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p36 | split | 7,809 | 1,067 | 5.67 | 0.0013 | 0.0007 | end_turn |
| claude-haiku-5-5 | kaigo_kyotsu_r0806 p41 | split・merged | 7,809 | 2,876 | 12.48 | 0.0022 | 0.0011 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p17 | merged | 7,833 | 7,305 | 25.17 | 0.0044 | 0.0022 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p20 | merged・split | 7,833 | 8,129 | 27.41 | 0.0048 | 0.0024 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p21 | merged・split | 7,833 | 6,050 | 21.28 | 0.0038 | 0.0019 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p31 | simple | 7,833 | 2,659 | 10.25 | 0.0021 | 0.0011 | end_turn |
| claude-haiku-5-5 | shogai_jigyosho_r0710 p90 | matrix | 7,833 | 33,191 | 98.5 | 0.0174 | 0.0087 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p80 | merged・split | 7,813 | 2,450 | 12.12 | 0.0401 | 0.0201 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p81 | merged・split | 7,813 | 2,787 | 13.45 | 0.0435 | 0.0217 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p84 | simple | 7,813 | 2,044 | 10.08 | 0.0361 | 0.0180 | end_turn |
| claude-sonnet-5-5 | kaigo_jigyosho_r0604 p110 | matrix | 7,813 | 5,777 | 26.17 | 0.0734 | 0.0367 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p12 | simple | 7,809 | 1,541 | 8.66 | 0.0310 | 0.0155 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p35 | merged・split | 7,809 | 2,287 | 11.78 | 0.0385 | 0.0192 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p36 | split | 7,809 | 402 | 4.09 | 0.0196 | 0.0098 | end_turn |
| claude-sonnet-5-5 | kaigo_kyotsu_r0806 p41 | split・merged | 7,809 | 1,353 | 8.17 | 0.0291 | 0.0146 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p17 | merged | 7,833 | 3,262 | 15.52 | 0.0483 | 0.0241 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p20 | merged・split | 7,833 | 3,581 | 16.81 | 0.0515 | 0.0257 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p21 | merged・split | 7,833 | 2,984 | 14.84 | 0.0455 | 0.0228 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p31 | simple | 7,833 | 1,642 | 9.09 | 0.0321 | 0.0160 | end_turn |
| claude-sonnet-5-5 | shogai_jigyosho_r0710 p90 | matrix | 7,833 | 8,136 | 36.67 | 0.0970 | 0.0485 | end_turn |

## モデル別 合計・1ページ平均

| モデル | ページ数 | 入力tok計 | 出力tok計 | 通常$計 | Batch$計 | 平均入力tok/頁 | 平均出力tok/頁 | 通常$/頁 | Batch$/頁 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| claude-haiku-5-5 | 13 | 101,653 | 92,852 | 0.0566 | 0.0283 | 7,819 | 7,142 | 0.0044 | 0.0022 |
| claude-sonnet-5-5 | 13 | 101,653 | 38,246 | 0.5858 | 0.2929 | 7,819 | 2,942 | 0.0451 | 0.0225 |

**この検証の合計（通常 API）: $0.6424**

## 全ページ処理した場合の見積もり

検証ページの平均トークン数 × ページ数で単純計算した値。表のないページ（目次・図・空白ページ）も含めて数えているので上振れ側の見積もり。検証ページは表が詰まったページを選んでいるため、1ページあたりの出力トークンも実際より多めに出ている可能性が高い。

| 範囲 | ページ数 | claude-haiku-5-5 通常$ | claude-haiku-5-5 Batch$ | claude-sonnet-5-5 通常$ | claude-sonnet-5-5 Batch$ |
|---|--:|--:|--:|--:|--:|
| 事業所向け（介護: 共通編＋サービス事業所編＋居宅介護支援事業所編 / 障害: 共通編＋事業所編） | 941 | 4.10 | 2.05 | 42.40 | 21.20 |
| 介護 manifest の spec 全部 | 2,533 | 11.03 | 5.51 | 114.13 | 57.07 |
| 障害 manifest の spec 全部 | 1,680 | 7.31 | 3.66 | 75.70 | 37.85 |
| 両分野 spec 全部 | 4,213 | 18.34 | 9.17 | 189.83 | 94.91 |

対象ページ数の内訳: kaigo_kyotsu_r0806=100, kaigo_jigyosho_r0604=237, kaigo_kyotaku_r0604=201, shogai_kyotsu_r0710=63, shogai_jigyosho_r0710=340
